from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from apps.branches.models import Branch
from apps.calllogs.models import CallLog
from apps.common.utils import get_branch_filter_ids
from apps.contacts.models import Contact
from apps.devices.models import Device
from apps.exports.models import ExportJob
from apps.leadmanagement.models import LeadManagement
from apps.monitoring.models import DeviceHealth


def _valid(value):
    return bool(value and str(value).strip() and value not in ("undefined", "null"))


def normalize_params(params=None):
    if not params:
        return {}
    if hasattr(params, "items"):
        return {key: value for key, value in params.items()}
    return dict(params)


def build_date_filter(params, field="call_time"):
    quick_date = params.get("quick_date")
    start_date = params.get("start_date")
    end_date = params.get("end_date")

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    query = Q()

    if quick_date == "today":
        query &= Q(**{f"{field}__gte": today_start})
    elif quick_date == "yesterday":
        yesterday_start = today_start - timedelta(days=1)
        query &= Q(**{f"{field}__gte": yesterday_start, f"{field}__lt": today_start})
    elif quick_date == "last_7_days":
        query &= Q(**{f"{field}__gte": now - timedelta(days=7)})
    else:
        if _valid(start_date):
            query &= Q(**{f"{field}__date__gte": start_date})
        if _valid(end_date):
            query &= Q(**{f"{field}__date__lte": end_date})

    return query


def build_dashboard_querysets(user, params):
    branch_ids = get_branch_filter_ids(user)
    branch_id = params.get("branch")
    branch_group_id = params.get("branch_group")
    lead_source = params.get("lead_source")
    date_filter = build_date_filter(params)

    User = get_user_model()
    calls_qs = CallLog.objects.all().order_by()
    health_qs = DeviceHealth.objects.select_related("device").all().order_by()
    branch_qs = Branch.objects.filter(is_active=True, is_deleted=False).order_by()
    device_qs = Device.objects.filter(is_deleted=False).order_by()
    lead_qs = LeadManagement.objects.all().order_by()
    contact_qs = Contact.objects.all().order_by()
    user_qs = User.objects.filter(is_active=True).order_by()
    export_qs = ExportJob.objects.all().order_by()

    if date_filter:
        calls_qs = calls_qs.filter(date_filter)

    if lead_source == "direct":
        lead_qs = lead_qs.filter(calllog__isnull=False)
        calls_qs = calls_qs.filter(lead__isnull=False)
    elif lead_source == "manual":
        lead_qs = lead_qs.filter(calllog__isnull=True)
        calls_qs = calls_qs.none()

    if branch_ids and branch_ids != ["NONE"]:
        calls_qs = calls_qs.filter(branch_id__in=branch_ids)
        health_qs = health_qs.filter(device__branch_id__in=branch_ids)
        branch_qs = branch_qs.filter(id__in=branch_ids)
        device_qs = device_qs.filter(branch_id__in=branch_ids)
        lead_qs = lead_qs.filter(branch_id__in=branch_ids)
        contact_qs = contact_qs.filter(call_logs__branch_id__in=branch_ids).distinct()
        user_qs = user_qs.filter(Q(branch_id__in=branch_ids) | Q(role__in=["admin", "super_admin"]))
        export_qs = export_qs.filter(user__branch_id__in=branch_ids)
    elif _valid(branch_id):
        calls_qs = calls_qs.filter(branch_id=branch_id)
        health_qs = health_qs.filter(device__branch_id=branch_id)
        branch_qs = branch_qs.filter(id=branch_id)
        device_qs = device_qs.filter(branch_id=branch_id)
        lead_qs = lead_qs.filter(branch_id=branch_id)
        contact_qs = contact_qs.filter(call_logs__branch_id=branch_id).distinct()
        user_qs = user_qs.filter(branch_id=branch_id)
        export_qs = export_qs.filter(user__branch_id=branch_id)
    elif _valid(branch_group_id):
        calls_qs = calls_qs.filter(branch__branch_group_id=branch_group_id)
        health_qs = health_qs.filter(device__branch__branch_group_id=branch_group_id)
        branch_qs = branch_qs.filter(branch_group_id=branch_group_id)
        device_qs = device_qs.filter(branch__branch_group_id=branch_group_id)
        lead_qs = lead_qs.filter(branch__branch_group_id=branch_group_id)
        contact_qs = contact_qs.filter(call_logs__branch__branch_group_id=branch_group_id).distinct()
        user_qs = user_qs.filter(branch__branch_group_id=branch_group_id)
        export_qs = export_qs.filter(user__branch__branch_group_id=branch_group_id)
    elif branch_ids == ["NONE"]:
        calls_qs = calls_qs.none()
        health_qs = health_qs.none()
        branch_qs = branch_qs.none()
        device_qs = device_qs.none()
        lead_qs = lead_qs.none()
        contact_qs = contact_qs.none()
        user_qs = user_qs.none()
        export_qs = export_qs.none()

    return {
        "branch_ids": branch_ids,
        "calls": calls_qs,
        "health": health_qs,
        "branches": branch_qs,
        "devices": device_qs,
        "leads": lead_qs,
        "contacts": contact_qs,
        "users": user_qs,
        "exports": export_qs,
    }


def today_calls_queryset(user, params):
    querysets = build_dashboard_querysets(user, {**params, "quick_date": None, "start_date": None, "end_date": None})
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return querysets["calls"].filter(call_time__gte=today_start)
