from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta, timezone as datetime_timezone
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounts.models import User, UserDeviceSession
from apps.branches.models import Branch, BranchGroups
from apps.devices.models import Device
from apps.calllogs.models import CallLog, MissedCallFollowUp
from apps.calllogs.filters import CallLogFilter
from apps.calllogs.serializers import CallLogListSerializer
from apps.calllogs.services import FollowUpService
from apps.calllogs.tasks import send_due_missed_call_reminders, send_missed_call_reminder


class CallLogTimeValidationTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            spa_name="Clock Test Branch",
            code="CLK-01",
            city="Pune",
            state="Maharashtra",
            postal_code=411001,
            address="Test address",
        )
        self.device = Device.objects.create(
            branch=self.branch,
            device_id="CLK-DEVICE-01",
            secret_key="secret-123",
            is_registered=True,
            android_id="android-clock-ok",
            fcm_token="fcm-token",
        )
        self.client = APIClient()
        self.headers = {
            "HTTP_X_DEVICE_ID": self.device.device_id,
            "HTTP_X_DEVICE_SECRET": self.device.secret_key,
        }

    def test_sync_accepts_current_call_time_ms(self):
        call_time = timezone.now() - timedelta(minutes=2)
        call_time_ms = int(call_time.timestamp() * 1000)

        response = self.client.post(
            "/api/v1/calllogs/sync/",
            [{
                "phone_number": "9876543210",
                "call_type": "incoming",
                "duration": 30,
                "sim_slot": 0,
                "call_time_ms": call_time_ms,
                "call_hash": "current-ms-hash",
            }],
            format="json",
            **self.headers,
        )

        self.assertEqual(response.status_code, 201)
        log = CallLog.objects.get(call_hash="current-ms-hash")
        expected = datetime.fromtimestamp(call_time_ms / 1000, tz=datetime_timezone.utc)
        self.assertFalse(log.is_time_invalid)
        self.assertEqual(log.invalid_time_reason, "")
        self.assertLess(abs((log.call_time - expected).total_seconds()), 1)

    def test_sync_flags_future_call_time_and_serializer_hides_future_label(self):
        future_call_time = timezone.now() + timedelta(days=180)
        future_call_time_ms = int(future_call_time.timestamp() * 1000)

        response = self.client.post(
            "/api/v1/calllogs/sync/",
            [{
                "phone_number": "9876543211",
                "call_type": "incoming",
                "duration": 45,
                "sim_slot": 0,
                "call_time_ms": future_call_time_ms,
                "call_hash": "future-ms-hash",
            }],
            format="json",
            **self.headers,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["invalid_time_count"], 1)
        log = CallLog.objects.get(call_hash="future-ms-hash")
        self.assertTrue(log.is_time_invalid)
        self.assertEqual(log.invalid_time_reason, "future_call_time")
        self.assertLessEqual(log.call_time, timezone.now() + timedelta(minutes=10))

        data = CallLogListSerializer(log).data
        self.assertEqual(data["call_time_label"], "Invalid device time")
        self.assertIn("future call time", data["call_time_warning"])

class MissedCallFollowUpTests(TestCase):
    def setUp(self):
        self.group = BranchGroups.objects.create(name="Test Group")
        self.branch = Branch.objects.create(
            spa_name="Test Branch",
            code="TB-01",
            city="Pune",
            state="Maharashtra",
            postal_code=411001,
            branch_group=self.group
        )
        self.device = Device.objects.create(
            branch=self.branch,
            device_id="SPA-DEV-101",
            is_registered=True
        )
        self.phone = "9876543210"

    def test_missed_then_customer_recall(self):
        # 1. Missed call happens
        time_missed = timezone.now() - timedelta(minutes=15)
        missed_log = CallLog.objects.create(
            branch=self.branch,
            device=self.device,
            phone_number=self.phone,
            call_type="missed",
            duration=0,
            sim_slot=1,
            call_time=time_missed,
            call_hash="hash1"
        )
        # Process the missed call
        FollowUpService.process_batch([missed_log])
        
        # Verify followup is created and not resolved
        followup = MissedCallFollowUp.objects.get(missed_call=missed_log)
        self.assertFalse(followup.is_followed_up)
        self.assertEqual(followup.sla_status, "MISSED")

        # 2. Customer recalls (incoming call)
        time_incoming = timezone.now()
        incoming_log = CallLog.objects.create(
            branch=self.branch,
            device=self.device,
            phone_number=self.phone,
            call_type="incoming",
            duration=60,
            sim_slot=1,
            call_time=time_incoming,
            call_hash="hash2"
        )
        # Process the incoming call
        FollowUpService.process_batch([incoming_log])

        # Verify followup is resolved with CUSTOMER_RECALL status
        followup.refresh_from_db()
        self.assertTrue(followup.is_followed_up)
        self.assertEqual(followup.sla_status, "CUSTOMER_RECALL")
        self.assertEqual(followup.followup_call, incoming_log)

    def test_customer_recall_already_exists(self):
        # 1. Customer calls first (incoming call)
        time_incoming = timezone.now()
        incoming_log = CallLog.objects.create(
            branch=self.branch,
            device=self.device,
            phone_number=self.phone,
            call_type="incoming",
            duration=60,
            sim_slot=1,
            call_time=time_incoming,
            call_hash="hash_incoming"
        )
        FollowUpService.process_batch([incoming_log])

        # 2. Missed call synced later but with call_time BEFORE the incoming call
        time_missed = time_incoming - timedelta(minutes=5)
        missed_log = CallLog.objects.create(
            branch=self.branch,
            device=self.device,
            phone_number=self.phone,
            call_type="missed",
            duration=0,
            sim_slot=1,
            call_time=time_missed,
            call_hash="hash_missed"
        )
        FollowUpService.process_batch([missed_log])

        # Verify followup is resolved immediately with CUSTOMER_RECALL
        followup = MissedCallFollowUp.objects.get(missed_call=missed_log)
        self.assertTrue(followup.is_followed_up)
        self.assertEqual(followup.sla_status, "CUSTOMER_RECALL")
        self.assertEqual(followup.followup_call, incoming_log)

    def test_missed_then_outgoing_good_sla(self):
        # 1. Missed call happens
        time_missed = timezone.now() - timedelta(minutes=5)
        missed_log = CallLog.objects.create(
            branch=self.branch,
            device=self.device,
            phone_number=self.phone,
            call_type="missed",
            duration=0,
            sim_slot=1,
            call_time=time_missed,
            call_hash="hash3"
        )
        FollowUpService.process_batch([missed_log])

        # 2. Outgoing call happens (5 minutes later)
        time_outgoing = time_missed + timedelta(minutes=5)
        outgoing_log = CallLog.objects.create(
            branch=self.branch,
            device=self.device,
            phone_number=self.phone,
            call_type="outgoing",
            duration=120,
            sim_slot=1,
            call_time=time_outgoing,
            call_hash="hash4"
        )
        FollowUpService.process_batch([outgoing_log])

        # Verify followup is resolved with GOOD SLA status
        followup = MissedCallFollowUp.objects.get(missed_call=missed_log)
        self.assertTrue(followup.is_followed_up)
        self.assertEqual(followup.sla_status, "GOOD")
        self.assertEqual(followup.followup_call, outgoing_log)

    @patch("apps.notifications.services.NotificationService.send_push", return_value=True)
    def test_missed_call_reminder_pushes_to_android_device(self, send_push):
        missed_log = CallLog.objects.create(
            branch=self.branch,
            device=self.device,
            phone_number=self.phone,
            call_type="missed",
            duration=0,
            sim_slot=1,
            call_time=timezone.now() - timedelta(minutes=12),
            call_hash="hash_reminder"
        )
        followup = MissedCallFollowUp.objects.create(
            missed_call=missed_log,
            branch=self.branch,
            is_followed_up=False,
        )

        result = send_missed_call_reminder(str(missed_log.id), 1)

        followup.refresh_from_db()
        self.assertIn("notification sent", result)
        self.assertEqual(followup.notification_step, 1)
        self.assertEqual(followup.sla_status, "OK")
        send_push.assert_called_once()
        kwargs = send_push.call_args.kwargs
        self.assertEqual(kwargs["recipient"], self.device)
        self.assertEqual(kwargs["notification_type"], "missed_call_followup")
        self.assertIn("Take follow-up on this number", kwargs["body"])
        self.assertEqual(kwargs["data"]["phone_number"], self.phone)
        self.assertEqual(kwargs["data"]["sla_step"], "1")

    @patch("apps.calllogs.tasks.send_missed_call_reminder.delay")
    def test_due_missed_call_sweep_queues_highest_due_step(self, delay):
        missed_log = CallLog.objects.create(
            branch=self.branch,
            device=self.device,
            phone_number=self.phone,
            call_type="missed",
            duration=0,
            sim_slot=1,
            call_time=timezone.now() - timedelta(minutes=35),
            call_hash="hash_sweep"
        )
        MissedCallFollowUp.objects.create(
            missed_call=missed_log,
            branch=self.branch,
            is_followed_up=False,
            notification_step=1,
        )

        result = send_due_missed_call_reminders()

        self.assertIn("Queued 1", result)
        delay.assert_called_once_with(str(missed_log.id), 2)


class CallLogSimFilterTests(TestCase):
    def setUp(self):
        group = BranchGroups.objects.create(name="SIM Filter Group")
        self.branch = Branch.objects.create(
            spa_name="SIM Filter Branch",
            code="SIM-01",
            city="Pune",
            state="Maharashtra",
            postal_code=411001,
            branch_group=group,
        )
        self.device = Device.objects.create(
            branch=self.branch,
            device_id="SPA-SIM-101",
            phone_name="Reception Phone",
            sim_1_number="9000000001",
            sim_2_number="9000000002",
            is_registered=True,
        )
        self.sim1_log = CallLog.objects.create(
            branch=self.branch,
            device=self.device,
            phone_number="8000000001",
            call_type="incoming",
            duration=30,
            sim_slot=1,
            call_time=timezone.now(),
            call_hash="sim-filter-1",
        )
        self.sim2_log = CallLog.objects.create(
            branch=self.branch,
            device=self.device,
            phone_number="8000000002",
            call_type="outgoing",
            duration=45,
            sim_slot=2,
            call_time=timezone.now(),
            call_hash="sim-filter-2",
        )

    def test_sim_number_filter_matches_the_sim_slot_used_by_the_call(self):
        sim1_results = CallLogFilter(
            data={"sim_number": self.device.sim_1_number},
            queryset=CallLog.objects.all(),
        ).qs
        sim2_results = CallLogFilter(
            data={"sim_number": self.device.sim_2_number},
            queryset=CallLog.objects.all(),
        ).qs

        self.assertQuerySetEqual(sim1_results, [self.sim1_log], transform=lambda item: item)
        self.assertQuerySetEqual(sim2_results, [self.sim2_log], transform=lambda item: item)

    def test_list_serializer_includes_both_sim_numbers_and_used_slot(self):
        data = CallLogListSerializer(self.sim2_log).data

        self.assertEqual(data["sim_slot"], 2)
        self.assertEqual(data["sim_1_number"], "9000000001")
        self.assertEqual(data["sim_2_number"], "9000000002")

    def test_general_search_matches_device_sim_number(self):
        results = CallLogFilter(
            data={"search": "9000000002"},
            queryset=CallLog.objects.all(),
        ).qs

        self.assertEqual(set(results), {self.sim1_log, self.sim2_log})


class CallLogDeviceScopedListTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            spa_name="Navi Mumbai",
            code="NM-01",
            city="Navi Mumbai",
            state="Maharashtra",
            postal_code=400703,
            address="Test address",
        )
        self.other_branch = Branch.objects.create(
            spa_name="Pune",
            code="PN-01",
            city="Pune",
            state="Maharashtra",
            postal_code=411001,
            address="Other address",
        )
        self.device_a = Device.objects.create(
            branch=self.branch,
            device_id="SPA-NM-A",
            secret_key="secret-a",
            is_registered=True,
        )
        self.device_b = Device.objects.create(
            branch=self.branch,
            device_id="SPA-NM-B",
            secret_key="secret-b",
            is_registered=True,
        )
        self.other_device = Device.objects.create(
            branch=self.other_branch,
            device_id="SPA-PN-C",
            secret_key="secret-c",
            is_registered=True,
        )
        self.device_a_log = self._create_log(self.device_a, "device-a-call")
        self.device_b_log = self._create_log(self.device_b, "device-b-call")
        self.other_log = self._create_log(self.other_device, "other-branch-call")

    def _create_log(self, device, call_hash):
        return CallLog.objects.create(
            branch=device.branch,
            device=device,
            phone_number="9876543210",
            call_type="incoming",
            duration=30,
            sim_slot=1,
            call_time=timezone.now(),
            call_hash=call_hash,
        )

    def _jwt_for_user(self, user, device_id="", platform="android"):
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        UserDeviceSession.objects.create(
            user=user,
            device_id=device_id,
            platform=platform,
            access_token_hash=UserDeviceSession.hash_token(access_token),
            refresh_token_hash=UserDeviceSession.hash_token(str(refresh)),
            is_active=True,
            status=UserDeviceSession.STATUS_ACTIVE,
            last_login=timezone.now(),
            last_activity=timezone.now(),
        )
        return access_token

    def _get_calllogs(self, token, params=None):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client.get("/api/v1/calllogs/", params or {})

    def _result_ids(self, response):
        self.assertEqual(response.status_code, 200)
        return {item["id"] for item in response.data["results"]}

    def test_android_spa_manager_sees_only_authenticated_session_device_calls(self):
        user = User.objects.create_user(
            email="spa@example.com",
            password="password",
            full_name="SPA Manager",
            role="spa_manager",
            branch=self.branch,
        )
        token = self._jwt_for_user(user, device_id=self.device_a.device_id)

        response = self._get_calllogs(token)

        self.assertEqual(self._result_ids(response), {str(self.device_a_log.id)})

    def test_client_device_filter_cannot_widen_android_session_scope(self):
        user = User.objects.create_user(
            email="spa-filter@example.com",
            password="password",
            full_name="SPA Manager",
            role="spa_manager",
            branch=self.branch,
        )
        token = self._jwt_for_user(user, device_id=self.device_a.device_id)

        response = self._get_calllogs(token, {"device": self.device_b.device_id})

        self.assertEqual(self._result_ids(response), set())

    def test_signed_headers_recover_call_logs_for_unbound_android_token(self):
        user = User.objects.create_user(
            email="spa-header@example.com",
            password="password",
            full_name="SPA Manager",
            role="spa_manager",
            branch=self.branch,
        )
        token = str(RefreshToken.for_user(user).access_token)

        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}",
            HTTP_X_DEVICE_ID=self.device_a.device_id,
            HTTP_X_DEVICE_SECRET=self.device_a.secret_key,
        )
        response = client.get("/api/v1/calllogs/")

        self.assertEqual(self._result_ids(response), {str(self.device_a_log.id)})

    def test_legacy_device_param_recovers_call_logs_for_old_unbound_token(self):
        user = User.objects.create_user(
            email="spa-legacy-calllogs@example.com",
            password="password",
            full_name="SPA Manager",
            role="spa_manager",
            branch=self.branch,
        )
        token = str(RefreshToken.for_user(user).access_token)

        response = self._get_calllogs(token, {"device": self.device_a.device_id})

        self.assertEqual(self._result_ids(response), {str(self.device_a_log.id)})

    def test_area_manager_keeps_branch_wide_call_log_access(self):
        user = User.objects.create_user(
            email="area@example.com",
            password="password",
            full_name="Area Manager",
            role="area_manager",
        )
        user.area_branches.add(self.branch)
        token = self._jwt_for_user(user, device_id=self.device_a.device_id, platform="web")

        response = self._get_calllogs(token)

        self.assertEqual(
            self._result_ids(response),
            {str(self.device_a_log.id), str(self.device_b_log.id)},
        )
