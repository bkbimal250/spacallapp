from django.db.models import Count, Q

from .cache import get_or_set
from .instrumentation import profile_segment
from .querysets import build_dashboard_querysets, normalize_params


class DashboardContactService:
    cache_timeout = 60

    @classmethod
    def get(cls, user, params=None, request=None, use_cache=True):
        params = normalize_params(params)
        if use_cache:
            return get_or_set("contacts", user, params, lambda: cls._calculate(user, params, request), cls.cache_timeout, request=request)
        return cls._calculate(user, params, request)

    @classmethod
    def _calculate(cls, user, params, request=None):
        with profile_segment("dashboard.contacts", request):
            contact_qs = build_dashboard_querysets(user, params)["contacts"]
            stats = contact_qs.aggregate(
                total_contacts=Count("id", distinct=True),
                contacts_with_email=Count("id", filter=Q(email__isnull=False), distinct=True),
                contacts_with_city=Count("id", filter=Q(city__isnull=False), distinct=True),
            )
            return {
                "total_contacts": stats["total_contacts"] or 0,
                "contacts_with_email": stats["contacts_with_email"] or 0,
                "contacts_with_city": stats["contacts_with_city"] or 0,
            }
