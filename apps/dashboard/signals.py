from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.accounts.models.user import User
from apps.branches.models import Branch
from apps.calllogs.models import CallLog
from apps.contacts.models import Contact
from apps.devices.models import Device
from apps.exports.models import ExportJob
from apps.leadmanagement.models import LeadManagement
from apps.monitoring.models import DeviceHealth

from .services.cache import invalidate_dashboard_cache


@receiver([post_save, post_delete], sender=CallLog)
def clear_dashboard_cache_on_calllog_write(**kwargs):
    invalidate_dashboard_cache("summary", "trends", "branches")


@receiver([post_save, post_delete], sender=Device)
@receiver([post_save, post_delete], sender=DeviceHealth)
def clear_dashboard_cache_on_device_write(**kwargs):
    invalidate_dashboard_cache("summary", "devices")


@receiver([post_save, post_delete], sender=Branch)
def clear_dashboard_cache_on_branch_write(**kwargs):
    invalidate_dashboard_cache("summary", "branches")


@receiver([post_save, post_delete], sender=LeadManagement)
def clear_dashboard_cache_on_lead_write(**kwargs):
    invalidate_dashboard_cache("summary")


@receiver([post_save, post_delete], sender=Contact)
def clear_dashboard_cache_on_contact_write(**kwargs):
    invalidate_dashboard_cache("summary", "contacts")


@receiver([post_save, post_delete], sender=ExportJob)
def clear_dashboard_cache_on_export_write(**kwargs):
    invalidate_dashboard_cache("summary", "exports")


@receiver([post_save, post_delete], sender=User)
def clear_dashboard_cache_on_user_write(**kwargs):
    invalidate_dashboard_cache("summary", "users")
