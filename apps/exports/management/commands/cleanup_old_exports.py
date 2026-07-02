from django.core.management.base import BaseCommand

from apps.exports.services import ExportRetentionService


class Command(BaseCommand):
    help = "Delete export jobs and files older than the retention window."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Delete exports older than this many days. Default: 30.",
        )

    def handle(self, *args, **options):
        days = options["days"]
        if days < 1:
            self.stderr.write(self.style.ERROR("--days must be at least 1"))
            return

        result = ExportRetentionService.cleanup_old_exports(days=days)
        self.stdout.write(
            self.style.SUCCESS(
                "Deleted {jobs} export jobs and {files} files older than {days} days. Cutoff: {cutoff}".format(
                    jobs=result["deleted_jobs"],
                    files=result["deleted_files"],
                    days=days,
                    cutoff=result["cutoff"].isoformat(),
                )
            )
        )
