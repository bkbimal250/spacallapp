import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import unquote, urlparse

from django.conf import settings
from django.utils import timezone

from .models import ExportJob
from .utils import ExportUtils
from .s3 import S3Service


class ExportService:
    @staticmethod
    def export_call_logs(data, format="csv"):
        headers = ["call_time", "phone_number", "duration", "call_type"]
        
        filename = f"export.{format}"
        file_path = f"/tmp/{filename}" # Check OS compatibility for path
        
        if format == "csv":
            content = ExportUtils.generate_csv(data, headers)
            # Write string content to file
            with open(filename, "w") as f:
                f.write(content)
        # Add other formats
        
        # Upload to S3
        url = S3Service.upload_file(filename)
        
        # Clean up
        if os.path.exists(filename):
            os.remove(filename)
            
        return url


class ExportRetentionService:
    EXPORT_MEDIA_DIR = "exports"

    @classmethod
    def export_dir(cls) -> Path:
        path = Path(settings.MEDIA_ROOT) / cls.EXPORT_MEDIA_DIR
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def safe_export_path(cls, filename: str | None) -> Path | None:
        if not filename:
            return None
        safe_name = Path(unquote(filename).replace("\\", "/")).name
        if not safe_name:
            return None
        return (cls.export_dir() / safe_name).resolve()

    @classmethod
    def path_from_file_url(cls, file_url: str | None) -> Path | None:
        if not file_url:
            return None

        media_path = urlparse(file_url).path or file_url
        media_prefix = urlparse(settings.MEDIA_URL).path.rstrip("/") + "/"
        if not media_path.startswith(media_prefix):
            return None

        relative_path = unquote(media_path[len(media_prefix):].lstrip("/")).replace("\\", "/")
        path = (Path(settings.MEDIA_ROOT) / Path(*Path(relative_path).parts)).resolve()
        export_root = cls.export_dir().resolve()
        if export_root not in path.parents and path != export_root:
            return None
        return path

    @classmethod
    def delete_export_file(cls, job: ExportJob) -> bool:
        file_path = cls.path_from_file_url(job.file_url) or cls.safe_export_path(job.file_name)
        if file_path and file_path.exists():
            file_path.unlink()
            return True
        return False

    @classmethod
    def cleanup_old_exports(cls, days: int = 30) -> dict:
        cutoff = timezone.now() - timedelta(days=days)
        jobs = ExportJob.objects.filter(created_at__lt=cutoff)
        deleted_files = 0
        deleted_jobs = 0

        for job in jobs.iterator(chunk_size=200):
            if cls.delete_export_file(job):
                deleted_files += 1
            job.delete()
            deleted_jobs += 1

        return {
            "cutoff": cutoff,
            "deleted_files": deleted_files,
            "deleted_jobs": deleted_jobs,
        }
    




