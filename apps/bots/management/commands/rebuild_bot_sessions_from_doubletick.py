from django.core.management.base import BaseCommand

from apps.bots.services import BotEngine
from apps.doubletick.models import DoubleTickConversation, DoubleTickMessage


class Command(BaseCommand):
    help = "Rebuild missing BotSession rows from existing DoubleTick conversations and inbound messages."

    def handle(self, *args, **options):
        counts = {"scanned": 0, "created": 0, "skipped": 0, "errors": 0}
        queryset = DoubleTickConversation.objects.select_related("customer", "channel", "current_lead").prefetch_related("bot_sessions")
        for conversation in queryset.iterator():
            counts["scanned"] += 1
            if conversation.bot_sessions.exists():
                counts["skipped"] += 1
                continue
            message = conversation.messages.filter(direction=DoubleTickMessage.Direction.INBOUND).order_by("created_at").first()
            if not message:
                counts["skipped"] += 1
                continue
            try:
                session = BotEngine.handle_incoming_message(conversation, conversation.current_lead, message)
                counts["created" if session else "skipped"] += 1
            except Exception as exc:
                counts["errors"] += 1
                self.stderr.write(f"error conversation={conversation.id}: {exc}")
        self.stdout.write("scanned={scanned} created={created} skipped={skipped} errors={errors}".format(**counts))
