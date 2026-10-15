from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event
from unittest.mock import patch

from django.conf import settings
from django.db import close_old_connections, connection
from django.test import TransactionTestCase, override_settings, skipUnlessDBFeature
from django.utils import timezone

from apps.branches.models import Branch
from apps.devices.models import Device
from apps.calllogs.models import CallLog, MissedCallFollowUp, MissedCallReminder
from apps.calllogs.tasks import schedule_missed_call_notifications, send_missed_call_reminder, send_due_missed_call_reminders
from apps.callrouting.models import RoutingRequest, RoutingWhatsAppMessage
from apps.callrouting.tasks import send_routing_whatsapp_message, process_call_log_routing
from apps.callrouting.provider import DoubleTickTransientError


class TaskSafetyTests(TransactionTestCase):
    def setUp(self):
        self.branch = Branch.objects.create(spa_name="Offline", code="OFF", city="Test", state="Test", postal_code=400001)
        self.device = Device.objects.create(branch=self.branch, device_id="offline", is_registered=True)
        self.call = CallLog.objects.create(branch=self.branch, device=self.device, phone_number="9876543210",
            call_type="missed", duration=0, sim_slot=1, call_time=timezone.now()-timedelta(minutes=12), call_hash="offline")
        self.followup = MissedCallFollowUp.objects.create(missed_call=self.call, branch=self.branch)
        self.push = patch("apps.notifications.services.NotificationService.send_push", return_value=True).start()
        self.provider = patch("apps.callrouting.tasks.DoubleTickTemplateProvider.send", return_value={
            "message_id": "offline-id", "provider_payload": {}}).start()
        self.addCleanup(patch.stopall)

    def age(self, minutes):
        self.call.call_time = timezone.now()-timedelta(minutes=minutes)
        self.call.save(update_fields=["call_time"])

    def message(self):
        request = RoutingRequest.objects.create(call_log=self.call, source_branch=self.branch,
            source_device=self.device, call_time=self.call.call_time, status="routed", normalized_phone="+919876543210")
        return RoutingWhatsAppMessage.objects.create(routing_request=request, recipient_phone="+919876543210",
            template_name="offline", idempotency_key="offline", status="queued", template_payload={"template_variables": ["a", "b", "c"]})

    def test_delayed_scheduler_uses_original_timestamp(self):
        self.age(35)
        with patch("apps.calllogs.tasks.send_missed_call_reminder.apply_async") as publish:
            self.assertEqual(schedule_missed_call_notifications(str(self.call.pk)), 2)
        self.assertEqual([c.kwargs["args"][1] for c in publish.call_args_list], [2, 3])
        self.assertEqual(publish.call_args_list[1].kwargs["eta"], self.call.call_time+timedelta(minutes=60))
        self.assertEqual(publish.call_args_list[1].kwargs["expires"], self.call.call_time+timedelta(minutes=90))

    def test_scheduler_and_repeated_sweep_share_reservations(self):
        with patch("apps.calllogs.tasks.send_missed_call_reminder.apply_async") as publish:
            schedule_missed_call_notifications(str(self.call.pk))
            schedule_missed_call_notifications(str(self.call.pk))
            send_due_missed_call_reminders()
            send_due_missed_call_reminders()
            self.assertEqual(publish.call_count, 3)

    def test_stale_future_invalid_resolved_and_missing_do_not_publish(self):
        with patch("apps.calllogs.tasks.send_missed_call_reminder.apply_async") as publish:
            for minutes in (91, -1):
                self.age(minutes)
                self.assertEqual(schedule_missed_call_notifications(str(self.call.pk)), 0)
                send_missed_call_reminder(str(self.call.pk), 1)
            self.age(12)
            self.call.is_time_invalid = True
            self.call.save(update_fields=["is_time_invalid"])
            schedule_missed_call_notifications(str(self.call.pk))
            self.call.is_time_invalid = False
            self.call.save(update_fields=["is_time_invalid"])
            self.followup.is_followed_up = True
            self.followup.save()
            schedule_missed_call_notifications(str(self.call.pk))
            call_id = str(self.call.pk)
            self.call.delete()
            schedule_missed_call_notifications(call_id)
            publish.assert_not_called()
        self.push.assert_not_called()

    def test_legacy_sender_rechecks_stale_call(self):
        self.age(91)
        send_missed_call_reminder(str(self.call.pk), 3)
        self.push.assert_not_called()

    def test_duplicate_send_is_claimed_once(self):
        send_missed_call_reminder(str(self.call.pk), 1)
        send_missed_call_reminder(str(self.call.pk), 1)
        self.push.assert_called_once()
        self.followup.refresh_from_db()
        self.assertEqual(self.followup.notification_step, 1)

    def test_failed_send_does_not_advance_or_blindly_retry(self):
        self.push.return_value = False
        send_missed_call_reminder(str(self.call.pk), 1)
        send_missed_call_reminder(str(self.call.pk), 1)
        self.followup.refresh_from_db()
        self.assertEqual(self.followup.notification_step, 0)
        self.assertEqual(self.followup.reminders.get().status, "failed")
        self.push.assert_called_once()

    def test_notification_progress_cannot_regress(self):
        self.age(65)
        send_missed_call_reminder(str(self.call.pk), 3)
        send_missed_call_reminder(str(self.call.pk), 1)
        send_missed_call_reminder(str(self.call.pk), 2)
        self.followup.refresh_from_db()
        self.assertEqual(self.followup.notification_step, 3)
        self.push.assert_called_once()

    def test_followup_resolved_during_send_keeps_resolved_sla(self):
        def resolve(**kwargs):
            MissedCallFollowUp.objects.filter(pk=self.followup.pk).update(is_followed_up=True, sla_status="CUSTOMER_RECALL")
            return True
        self.push.side_effect = resolve
        send_missed_call_reminder(str(self.call.pk), 1)
        self.followup.refresh_from_db()
        self.assertEqual(self.followup.sla_status, "CUSTOMER_RECALL")

    def test_abandoned_reminder_requires_reconciliation(self):
        MissedCallReminder.objects.create(followup=self.followup, step=1, status="sending", lease_until=timezone.now()-timedelta(seconds=1))
        send_missed_call_reminder(str(self.call.pk), 1)
        self.assertEqual(self.followup.reminders.get().status, "ambiguous")
        self.push.assert_not_called()

    def test_publish_failure_can_be_recovered_without_new_claim(self):
        with patch("apps.calllogs.tasks.send_missed_call_reminder.apply_async", side_effect=RuntimeError("offline broker")):
            schedule_missed_call_notifications(str(self.call.pk), due_only=True)
        MissedCallReminder.objects.update(lease_until=timezone.now()-timedelta(seconds=1))
        with patch("apps.calllogs.tasks.send_missed_call_reminder.apply_async") as publish:
            send_due_missed_call_reminders()
            publish.assert_called_once()
        self.assertEqual(MissedCallReminder.objects.count(), 1)

    @override_settings(MISSED_CALL_SWEEP_BATCH_SIZE=1)
    def test_sweep_is_bounded_and_reserved_rows_do_not_starve_next_call(self):
        other = CallLog.objects.create(branch=self.branch, device=self.device, phone_number="9876543211",
            call_type="missed", duration=0, sim_slot=1, call_time=self.call.call_time, call_hash="other")
        MissedCallFollowUp.objects.create(missed_call=other, branch=self.branch)
        with patch("apps.calllogs.tasks.send_missed_call_reminder.apply_async") as publish:
            send_due_missed_call_reminders()
            self.assertEqual(publish.call_count, 1)
            send_due_missed_call_reminders()
            self.assertEqual(publish.call_count, 2)

    def test_flags_rechecked_after_whatsapp_queued(self):
        message = self.message()
        for flag, value in [("ENABLE_CALL_ROUTING", False), ("ENABLE_CALL_ROUTING_WHATSAPP", False), ("CALL_ROUTING_DRY_RUN", True)]:
            with override_settings(**{flag: value}):
                self.assertEqual(send_routing_whatsapp_message(str(message.pk))["status"], "disabled")
        self.provider.assert_not_called()

    def test_whatsapp_timeout_is_ambiguous_and_never_retried(self):
        message = self.message()
        self.provider.side_effect = DoubleTickTransientError("timeout")
        self.assertEqual(send_routing_whatsapp_message(str(message.pk))["status"], "ambiguous")
        send_routing_whatsapp_message(str(message.pk))
        self.provider.assert_called_once()

    def test_whatsapp_inflight_and_abandoned_claims_never_resend(self):
        message = self.message()
        message.status = "sending"
        message.save()
        send_routing_whatsapp_message(str(message.pk))
        RoutingWhatsAppMessage.objects.filter(pk=message.pk).update(updated_at=timezone.now()-timedelta(minutes=10))
        self.assertEqual(send_routing_whatsapp_message(str(message.pk))["status"], "ambiguous")
        self.provider.assert_not_called()

    def test_whatsapp_stale_or_recipient_changed_is_cancelled(self):
        message = self.message()
        self.age(91)
        self.assertEqual(send_routing_whatsapp_message(str(message.pk))["status"], "cancelled")
        self.provider.assert_not_called()

    def test_routing_task_rejects_old_call_before_routing(self):
        self.age(91)
        with patch("apps.callrouting.tasks.RoutingService.process_call_log") as route:
            self.assertEqual(process_call_log_routing(str(self.call.pk))["status"], "ineligible")
            route.assert_not_called()

    def test_whatsapp_success_duplicate_does_not_send(self):
        message = self.message()
        self.assertEqual(send_routing_whatsapp_message(str(message.pk))["status"], "sent")
        self.assertEqual(send_routing_whatsapp_message(str(message.pk))["status"], "already_sent")
        self.provider.assert_called_once()

    @skipUnlessDBFeature("has_select_for_update")
    def test_concurrent_whatsapp_claims(self):
        message = self.message()
        entered, release = Event(), Event()
        def provider(*args):
            entered.set()
            if not release.wait(5):
                raise RuntimeError("test timed out")
            return {"message_id": "concurrent", "provider_payload": {}}
        self.provider.side_effect = provider
        def run():
            close_old_connections()
            try:
                return send_routing_whatsapp_message(str(message.pk))
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(run)
            try:
                self.assertTrue(entered.wait(5))
                self.assertEqual(pool.submit(run).result(timeout=5)["status"], "sending")
            finally:
                release.set()
            first.result(timeout=5)
        self.provider.assert_called_once()

    @skipUnlessDBFeature("has_select_for_update")
    def test_concurrent_reminder_claims(self):
        entered, release = Event(), Event()
        def push(**kwargs):
            entered.set()
            if not release.wait(5):
                raise RuntimeError("test timed out")
            return True
        self.push.side_effect = push
        def run():
            close_old_connections()
            try:
                return send_missed_call_reminder(str(self.call.pk), 1)
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(run)
            try:
                self.assertTrue(entered.wait(5))
                self.assertIn("in progress", pool.submit(run).result(timeout=5))
            finally:
                release.set()
            first.result(timeout=5)
        self.push.assert_called_once()

    def test_application_entry_points_bind_project_app_in_fresh_processes(self):
        import os
        import subprocess
        import sys
        for entry in ("config.wsgi", "config.asgi"):
            env = dict(os.environ, DJANGO_SETTINGS_MODULE="config.settings.test_tasks",
                       CELERY_BROKER_URL="memory://", CELERY_RESULT_BACKEND="cache+memory://")
            code = (
                "import socket; "
                "socket.socket.connect=lambda *a, **k: (_ for _ in ()).throw(RuntimeError('network forbidden')); "
                f"import {entry}; "
                "from config import celery_app; "
                "from apps.calllogs.tasks import schedule_missed_call_notifications as task; "
                "assert task.app is celery_app; "
                "assert task.app.conf.broker_url == 'memory://'; "
                "assert task.app.amqp.router.route({}, task.name)['queue'].name == 'calllog_offline_test'"
            )
            result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_real_app_binding_and_routed_memory_broker_publish(self):
        from config import celery_app
        from kombu import Connection
        from celery.signals import before_task_publish
        celery_app.autodiscover_tasks(force=True)
        self.assertIs(schedule_missed_call_notifications.app, celery_app)
        self.assertIs(process_call_log_routing.app, celery_app)
        self.assertEqual(celery_app.conf.broker_url, "memory://")
        seen = []
        def capture(sender=None, routing_key=None, **kwargs):
            seen.append((sender, routing_key))
        before_task_publish.connect(capture, weak=False)
        try:
            schedule_missed_call_notifications.apply_async(args=(str(self.call.pk),))
            process_call_log_routing.apply_async(args=(str(self.call.pk),))
        finally:
            before_task_publish.disconnect(capture)
        self.assertEqual([key for _, key in seen], [settings.CELERY_TASK_DEFAULT_QUEUE]*2)
        with Connection("memory://") as broker:
            queue = broker.SimpleQueue(settings.CELERY_TASK_DEFAULT_QUEUE)
            self.assertGreaterEqual(queue.qsize(), 2)
            queue.clear()
            queue.close()
