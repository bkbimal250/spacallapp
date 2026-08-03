from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone

from apps.branches.models import Branch
from apps.calllogs.models import CallLog
from apps.contacts.models import Contact
from apps.devices.models import Device
from apps.exports.models import ExportJob
from apps.leadmanagement.models import LeadManagement
from apps.monitoring.models import DeviceHealth

from ..models import DashboardStatistic


class DashboardStatisticsService:
    @staticmethod
    def refresh_for_date(target_date=None):
        target_date = target_date or timezone.localdate()
        branches = Branch.objects.filter(is_active=True, is_deleted=False).only("id")
        for branch in branches.iterator(chunk_size=200):
            DashboardStatisticsService.refresh_branch(branch, target_date)

    @staticmethod
    def refresh_branch(branch, target_date=None):
        target_date = target_date or timezone.localdate()
        day_start = timezone.make_aware(datetime.combine(target_date, time.min), timezone.get_current_timezone())
        day_end = day_start + timedelta(days=1)
        User = get_user_model()

        calls = CallLog.objects.filter(branch=branch, call_time__gte=day_start, call_time__lt=day_end)
        call_stats = calls.aggregate(
            incoming=Count("id", filter=Q(call_type="incoming")),
            outgoing=Count("id", filter=Q(call_type="outgoing")),
            missed=Count("id", filter=Q(call_type="missed")),
            total_calls=Count("id"),
            avg_duration=Avg("duration"),
        )
        total_calls = call_stats["total_calls"] or 0
        completed = (call_stats["incoming"] or 0) + (call_stats["outgoing"] or 0)
        conversion_rate = round((completed / total_calls * 100) if total_calls else 0, 2)

        DashboardStatistic.objects.update_or_create(
            branch=branch,
            date=target_date,
            defaults={
                "incoming": call_stats["incoming"] or 0,
                "outgoing": call_stats["outgoing"] or 0,
                "missed": call_stats["missed"] or 0,
                "total_calls": total_calls,
                "active_devices": DeviceHealth.objects.filter(device__branch=branch, is_online=True).count(),
                "total_devices": Device.objects.filter(branch=branch, is_deleted=False).count(),
                "total_contacts": Contact.objects.filter(call_logs__branch=branch).distinct().count(),
                "total_users": User.objects.filter(is_active=True, branch=branch).count(),
                "total_leads": LeadManagement.objects.filter(branch=branch).count(),
                "total_exports": ExportJob.objects.filter(user__branch=branch).count(),
                "avg_duration": call_stats["avg_duration"] or 0,
                "conversion_rate": conversion_rate,
            },
        )

    @staticmethod
    def aggregate_for_branches(branch_ids, target_date=None):
        target_date = target_date or timezone.localdate()
        queryset = DashboardStatistic.objects.filter(date=target_date)
        if branch_ids:
            queryset = queryset.filter(branch_id__in=branch_ids)

        stats = queryset.aggregate(
            total_calls=Sum("total_calls"),
            today_incoming_calls=Sum("incoming"),
            today_outgoing_calls=Sum("outgoing"),
            today_missed_calls=Sum("missed"),
            active_devices=Sum("active_devices"),
            total_devices=Sum("total_devices"),
            total_contacts=Sum("total_contacts"),
            total_users=Sum("total_users"),
            total_leads=Sum("total_leads"),
            total_exports=Sum("total_exports"),
            avg_duration=Avg("avg_duration"),
        )
        return {key: (value or 0) for key, value in stats.items()}
