from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.utils import timezone

from .models import Branch, BranchOperatingHours


class BranchService:

    @staticmethod
    def create_branch(data):
        return Branch.objects.create(**data)

    @staticmethod
    def update_branch(instance, data):
        for key, value in data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    @staticmethod
    def deactivate_branch(instance):
        instance.is_active = False
        instance.save()
        return instance


class BranchOperatingHoursService:
    """
    Evaluate BranchOperatingHours safely.

    Safe default: if no active hours are configured for the relevant day, the
    branch is considered closed.
    """

    @staticmethod
    def _zone(tz_name):
        try:
            return ZoneInfo(tz_name or settings.TIME_ZONE)
        except ZoneInfoNotFoundError:
            return ZoneInfo(settings.TIME_ZONE)

    @classmethod
    def _localize(cls, value, tz_name):
        if value is None:
            value = timezone.now()
        zone = cls._zone(tz_name)
        if timezone.is_naive(value):
            value = timezone.make_aware(value, zone)
        return value.astimezone(zone)

    @staticmethod
    def _matches_hours(hours, local_dt):
        if not hours or not hours.is_active or hours.is_deleted or hours.is_closed:
            return False
        if hours.is_24_hours:
            return True
        if not hours.opens_at or not hours.closes_at:
            return False

        local_time = local_dt.time()
        if hours.opens_at <= hours.closes_at:
            return hours.opens_at <= local_time < hours.closes_at
        return local_time >= hours.opens_at or local_time < hours.closes_at

    @classmethod
    def get_applicable_hours(cls, branch, at_datetime=None):
        hours_qs = BranchOperatingHours.objects.filter(
            branch=branch,
            is_active=True,
            is_deleted=False,
        )
        for hours in hours_qs:
            local_dt = cls._localize(at_datetime, hours.timezone)
            local_time = local_dt.time()
            local_weekday = local_dt.weekday()

            if hours.weekday == local_weekday and cls._matches_hours(hours, local_dt):
                return hours

            if hours.is_overnight:
                previous_weekday = (local_weekday - 1) % 7
                if hours.weekday == previous_weekday and local_time < hours.closes_at:
                    return hours
        return None

    @classmethod
    def is_branch_open(cls, branch, at_datetime=None):
        if not branch or not branch.is_active or getattr(branch, "is_deleted", False):
            return False
        return cls.get_applicable_hours(branch, at_datetime) is not None
