from django.core.management.base import BaseCommand

from apps.doubletick.models import DoubleTickConversation, DoubleTickLead
from apps.doubletick.services import normalize_area_text


GENERIC_VALUES = {
    "hello",
    "hi",
    "hey",
    "hii",
    "hiii",
    "ok",
    "okay",
    "namaste",
    "नमस्ते",
    "hindi me message kijiye",
    "hindi mein message kijiye",
    "please message in hindi",
    "call me",
}


class Command(BaseCommand):
    help = "Clear generic greeting/instruction text incorrectly saved as DoubleTick raw_area."

    def handle(self, *args, **options):
        normalized = {normalize_area_text(item) for item in GENERIC_VALUES}
        counts = {"scanned": 0, "created": 0, "skipped": 0, "errors": 0}
        for model in [DoubleTickConversation, DoubleTickLead]:
            for obj in model.objects.exclude(raw_area="").iterator():
                counts["scanned"] += 1
                if normalize_area_text(obj.raw_area) not in normalized:
                    counts["skipped"] += 1
                    continue
                try:
                    obj.raw_area = ""
                    if hasattr(obj, "area") and normalize_area_text(getattr(obj, "area", "")) in normalized:
                        obj.area = ""
                        obj.save(update_fields=["raw_area", "area", "updated_at"])
                    else:
                        obj.save(update_fields=["raw_area", "updated_at"])
                    counts["created"] += 1
                except Exception as exc:
                    counts["errors"] += 1
                    self.stderr.write(f"error {model.__name__}={obj.id}: {exc}")
        self.stdout.write("scanned={scanned} fixed={created} skipped={skipped} errors={errors}".format(**counts))
