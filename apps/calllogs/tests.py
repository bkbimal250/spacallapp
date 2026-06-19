from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
from apps.branches.models import Branch, BranchGroups
from apps.devices.models import Device
from apps.calllogs.models import CallLog, MissedCallFollowUp
from apps.calllogs.services import FollowUpService
from apps.calllogs.tasks import send_due_missed_call_reminders, send_missed_call_reminder

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
