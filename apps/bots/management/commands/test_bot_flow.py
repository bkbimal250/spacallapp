from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.bots.services import BotEngine
from apps.doubletick.models import DoubleTickConversation, DoubleTickLead, DoubleTickMessage


class Command(BaseCommand):
    help = "Run a safe local bot-flow test against an existing DoubleTick lead or conversation."

    def add_arguments(self, parser):
        parser.add_argument("--lead-id", required=False)
        parser.add_argument("--conversation-id", required=False)
        parser.add_argument("--text", default="Hello")

    def handle(self, *args, **options):
        lead = None
        conversation = None
        if options.get("lead_id"):
            lead = DoubleTickLead.objects.select_related("conversation", "customer").get(id=options["lead_id"])
            conversation = lead.conversation
        elif options.get("conversation_id"):
            conversation = DoubleTickConversation.objects.select_related("customer", "current_lead").get(id=options["conversation_id"])
            lead = conversation.current_lead
        if not conversation:
            raise CommandError("Provide --lead-id or --conversation-id.")
        message = DoubleTickMessage.objects.create(
            conversation=conversation,
            lead=lead,
            customer=conversation.customer,
            direction=DoubleTickMessage.Direction.INBOUND,
            origin=DoubleTickMessage.Origin.CUSTOMER,
            message_type="text",
            text=options["text"],
            customer_number=conversation.customer.phone_number,
            waba_number=conversation.channel.waba_number if conversation.channel else "",
            message_timestamp=timezone.now(),
            received_at=timezone.now(),
            raw_payload={"source": "test_bot_flow"},
        )
        session = BotEngine.handle_incoming_message(conversation, lead, message)
        self.stdout.write(f"session={session.id if session else ''} status={session.status if session else 'none'}")
