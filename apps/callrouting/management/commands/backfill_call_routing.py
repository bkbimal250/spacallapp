from django.core.management.base import BaseCommand
from django.db.models import Exists, OuterRef, Q

from apps.calllogs.models import CallLog
from apps.callrouting.models import RoutingRequest
from apps.callrouting.services import RoutingService
from apps.callrouting.whatsapp import RoutingWhatsAppService


class Command(BaseCommand):
    help = "Backfill CallRouting requests for existing unprocessed CallLogs."

    def add_arguments(self, parser):
        parser.add_argument("--date-from", dest="date_from", help="Call time date lower bound, YYYY-MM-DD.")
        parser.add_argument("--date-to", dest="date_to", help="Call time date upper bound, YYYY-MM-DD.")
        parser.add_argument("--branch", dest="branch", help="Filter source branch name/code contains this value.")
        parser.add_argument("--phone", dest="phone", help="Filter phone number contains this value.")
        parser.add_argument("--types", nargs="+", default=["missed", "incoming"], help="Call types to process.")
        parser.add_argument("--limit", type=int, default=500, help="Maximum call logs to process.")
        parser.add_argument("--dry-run", action="store_true", help="Show matching call logs without creating routing records.")
        parser.add_argument("--prepare-whatsapp", action="store_true", help="Also prepare WhatsApp records after routing.")

    def handle(self, *args, **options):
        existing = RoutingRequest.objects.filter(call_log_id=OuterRef("pk"))
        queryset = (
            CallLog.objects.select_related("branch", "device", "contact")
            .annotate(has_routing=Exists(existing))
            .filter(has_routing=False, call_type__in=options["types"])
            .order_by("call_time")
        )

        if options.get("date_from"):
            queryset = queryset.filter(call_time__date__gte=options["date_from"])
        if options.get("date_to"):
            queryset = queryset.filter(call_time__date__lte=options["date_to"])
        if options.get("branch"):
            branch = options["branch"]
            queryset = queryset.filter(Q(branch__spa_name__icontains=branch) | Q(branch__code__icontains=branch))
        if options.get("phone"):
            queryset = queryset.filter(phone_number__icontains=options["phone"])

        limit = max(0, options["limit"] or 0)
        call_logs = list(queryset[:limit])
        if options["dry_run"]:
            for call_log in call_logs:
                self.stdout.write(f"{call_log.id} {call_log.call_time} {call_log.call_type} {call_log.phone_number} {call_log.branch}")
            self.stdout.write(self.style.WARNING(f"Dry run only. Matched {len(call_logs)} unprocessed call logs."))
            return

        routed = skipped = failed = whatsapp = 0
        for call_log in call_logs:
            try:
                request = RoutingService.process_call_log(call_log)
                if request.status == RoutingRequest.Status.ROUTED:
                    routed += 1
                elif request.status == RoutingRequest.Status.SKIPPED:
                    skipped += 1
                elif request.status == RoutingRequest.Status.FAILED:
                    failed += 1
                if options["prepare_whatsapp"]:
                    message = RoutingWhatsAppService.prepare_for_request(request)
                    if message:
                        whatsapp += 1
            except Exception as exc:
                failed += 1
                self.stderr.write(self.style.ERROR(f"{call_log.id}: {exc}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Processed {len(call_logs)} call logs. routed={routed} skipped={skipped} failed={failed} whatsapp_prepared={whatsapp}"
            )
        )
