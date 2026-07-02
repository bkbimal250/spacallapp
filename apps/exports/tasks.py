from celery import shared_task
from .services import ExportRetentionService, ExportService
from apps.calllogs.models import CallLog

@shared_task
def export_logs_task(branch_id, format="csv"):
    # Fetch data
    logs = CallLog.objects.filter(branch_id=branch_id).values(
        "call_time", "phone_number", "duration", "call_type"
    )
    
    url = ExportService.export_call_logs(logs, format)
    
    # Notify user? Save Export record?
    # For now, just return URL
    return url


@shared_task
def cleanup_old_exports_task(days=30):
    result = ExportRetentionService.cleanup_old_exports(days=days)
    return {
        "deleted_jobs": result["deleted_jobs"],
        "deleted_files": result["deleted_files"],
        "cutoff": result["cutoff"].isoformat(),
    }
