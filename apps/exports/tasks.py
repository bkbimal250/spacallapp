from celery import shared_task
from .services import ExportService
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
