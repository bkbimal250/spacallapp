from collections import Counter

from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from apps.bots.models import Bot, BotApiCallLog, BotIntegration, BotSheetSyncLog, BotTrigger
from apps.doubletick.channel_setup import normalize_waba_number
from apps.doubletick.integrations.doubletick import first_value
from apps.doubletick.models import (
    DoubleTickAreaAlias,
    DoubleTickChannel,
    DoubleTickConversation,
    DoubleTickLead,
    DoubleTickLeadArea,
    DoubleTickLeadAreaBranch,
    DoubleTickLeadVisibility,
    DoubleTickTeamMemberMapping,
    DoubleTickWebhookLog,
)


WABA_PATHS = [
    "wabaNumber",
    "waba_number",
    "channel.waba_number",
    "data.wabaNumber",
    "data.channel.waba_number",
]


class Command(BaseCommand):
    help = "Audit DoubleTick, bot routing, channel setup, and lead assignment health."

    def _line(self, label, value):
        self.stdout.write(f"{label:<48} {value}")

    def _latest_webhook_wabas(self):
        counter = Counter()
        for payload in DoubleTickWebhookLog.objects.order_by("-created_at").values_list("payload", flat=True)[:500]:
            if not isinstance(payload, dict):
                continue
            for path in WABA_PATHS:
                value = normalize_waba_number(first_value(payload, [path]))
                if value:
                    counter[value] += 1
        return counter

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("DoubleTick Setup Audit"))
        self.stdout.write("=" * 72)

        channel_wabas = set(DoubleTickChannel.objects.exclude(waba_number="").values_list("waba_number", flat=True))
        active_channel_wabas = set(DoubleTickChannel.objects.filter(is_active=True).exclude(waba_number="").values_list("waba_number", flat=True))
        duplicate_wabas = (
            DoubleTickChannel.objects.exclude(waba_number="")
            .values("waba_number")
            .annotate(total=Count("id"))
            .filter(total__gt=1)
        )
        webhook_wabas = self._latest_webhook_wabas()
        missing_wabas = sorted(set(webhook_wabas.keys()) - channel_wabas)

        self._line("Total DoubleTickChannel", DoubleTickChannel.objects.count())
        self._line("Active DoubleTickChannel", DoubleTickChannel.objects.filter(is_active=True).count())
        self._line("Channels missing waba_number", DoubleTickChannel.objects.filter(Q(waba_number="") | Q(waba_number__isnull=True)).count())
        self._line("Duplicate waba_number records", ", ".join(f"{row['waba_number']} ({row['total']})" for row in duplicate_wabas) or "None")
        self._line("Latest webhook WABA numbers", ", ".join(f"{number} ({count})" for number, count in webhook_wabas.most_common(20)) or "None found")
        self._line("Webhook WABAs missing channel", ", ".join(missing_wabas) or "None")
        self._line("Active channel WABAs", ", ".join(sorted(active_channel_wabas)) or "None")
        self.stdout.write("")

        self._line("DoubleTickTeamMemberMapping count", DoubleTickTeamMemberMapping.objects.count())
        self._line("DoubleTickLeadArea count", DoubleTickLeadArea.objects.count())
        self._line("DoubleTickAreaAlias count", DoubleTickAreaAlias.objects.count())
        self._line("DoubleTickLeadAreaBranch count", DoubleTickLeadAreaBranch.objects.count())
        self._line("Conversations without current_lead", DoubleTickConversation.objects.filter(current_lead__isnull=True).count())
        self._line("Leads without matched_area", DoubleTickLead.objects.filter(matched_area__isnull=True).count())
        self._line("Leads without visibility", DoubleTickLead.objects.filter(visibilities__isnull=True).distinct().count())
        failed_logs = DoubleTickWebhookLog.objects.exclude(Q(error_message="") | Q(error_message__isnull=True))
        self._line("Failed webhook logs", failed_logs.count())
        self._line("processed=False webhook logs", DoubleTickWebhookLog.objects.filter(processed=False).count())
        recent_errors = failed_logs.order_by("-created_at")[:5]
        self._line("Recent webhook/API errors", "; ".join(f"{log.created_at:%Y-%m-%d %H:%M}: {(log.error_message or '')[:90]}" for log in recent_errors) or "None")
        self.stdout.write("")

        self._line("Bot count", Bot.objects.count())
        self._line("Active bot count", Bot.objects.filter(is_active=True).count())
        self._line("Bot triggers count", BotTrigger.objects.count())
        self._line("Default active bot trigger exists", "YES" if BotTrigger.objects.filter(is_default=True, is_active=True, bot__is_active=True).exists() else "NO")
        channel_trigger_count = BotTrigger.objects.filter(channel__isnull=False, is_active=True, bot__is_active=True).count()
        self._line("Active channel-specific triggers", channel_trigger_count)
        self.stdout.write("")

        self._line("BotIntegration total", BotIntegration.objects.count())
        self._line("Google Sheets integrations", BotIntegration.objects.filter(integration_type="google_sheets").count())
        self._line("Webhook API integrations", BotIntegration.objects.filter(integration_type="webhook_api").count())
        self._line("Internal API integrations", BotIntegration.objects.filter(integration_type="internal_api").count())
        self._line("Disabled integrations", BotIntegration.objects.filter(is_active=False).count())
        self._line("Integrations missing credentials", BotIntegration.objects.filter(credentials={}).count())
        self._line("Recent failed API calls", BotApiCallLog.objects.filter(success=False).count())
        self._line("Recent failed sheet syncs", BotSheetSyncLog.objects.filter(success=False).count())

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("DoubleTick Setup Checklist"))
        checklist = [
            "Webhook URL configured in DoubleTick dashboard",
            "Required DoubleTick dashboard triggers selected",
            "All selected WABA/API channels exist as DoubleTickChannel records",
            "Active default bot exists",
            "Default active bot trigger exists",
            "Channel-specific bot triggers exist for Rajasthan/Gujarat/Bangalore if required",
            "LeadArea records exist",
            "Area aliases exist",
            "Lead area to branch mappings exist",
            "Team member mappings exist",
            "Android pending leads API reviewed",
            "CRM reply API reviewed",
            "processed=False webhook logs are zero or reviewed",
        ]
        for item in checklist:
            self.stdout.write(f"[ ] {item}")
