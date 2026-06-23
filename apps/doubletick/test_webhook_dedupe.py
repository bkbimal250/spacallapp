from django.test import TestCase
from apps.doubletick.services import create_or_update_lead_from_webhook
from apps.doubletick.models import DoubleTickWebhookLog

class WebhookDedupeTests(TestCase):
    def test_duplicate_webhook_is_skipped(self):
        payload = {"event_id": "evt-123", "type": "incoming_customer_message", "message": {"text": "hello"}}
        # first processing
        lead, log = create_or_update_lead_from_webhook(payload)
        self.assertIsNotNone(log)
        self.assertTrue(log.created_at is not None)
        # mark the first as processed (simulate normal flow)
        log.processed = True
        log.save()
        # second webhook with same event id should be short-circuited
        lead2, log2 = create_or_update_lead_from_webhook(payload)
        self.assertIsNotNone(log2)
        self.assertEqual(log2.error_message, "duplicate_event_skipped")
