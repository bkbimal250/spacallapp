import os
import sys
import django

# Add the project root to sys.path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.leadmanagement.models import LeadManagement
from django.db.models import Count

# Find calllogs with multiple leads
duplicates = LeadManagement.objects.values('calllog').annotate(count=Count('id')).filter(count__gt=1, calllog__isnull=False)
print(f"Found {duplicates.count()} calllogs with duplicate leads.")

for dup in duplicates:
    calllog_id = dup['calllog']
    lead_ids = list(LeadManagement.objects.filter(calllog_id=calllog_id).order_by('created_at').values_list('id', flat=True))
    
    # Keep the first one, delete the rest
    to_delete_ids = lead_ids[1:]
    deleted_count = len(to_delete_ids)
    LeadManagement.objects.filter(id__in=to_delete_ids).delete()
    print(f"Deleted {deleted_count} duplicate leads for calllog {calllog_id}")

print("Cleanup complete.")
