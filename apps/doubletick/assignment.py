from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.branches.models import Branch
from apps.devices.models import Device

from .models import DoubleTickLead


def find_matching_branch(city, area):
    """
    Match a lead to an active branch by city/area.

    Exact city+area matching is preferred. If no area match exists, the first
    active branch in the city is returned so the lead can still be routed.
    """
    city = (city or "").strip()
    area = (area or "").strip()
    if not city and not area:
        return None

    active_branches = Branch.objects.filter(is_active=True)
    if hasattr(Branch, "is_deleted"):
        active_branches = active_branches.filter(is_deleted=False)

    if city and area:
        branch = active_branches.filter(city__iexact=city, area__iexact=area).order_by("spa_name").first()
        if branch:
            return branch

    if city:
        branch = active_branches.filter(city__iexact=city).order_by("spa_name").first()
        if branch:
            return branch

    if area:
        return active_branches.filter(area__iexact=area).order_by("spa_name").first()
    return None


def assign_lead_to_user_or_device(lead):
    """
    Assign the lead using the requested priority order.

    The function updates only DoubleTick lead fields and relies on existing CRM
    branch/user/device relationships for routing.
    """
    branch = lead.assigned_branch or find_matching_branch(lead.city, lead.area)
    if not branch:
        lead.status = DoubleTickLead.Status.UNASSIGNED
        lead.save(update_fields=["status", "updated_at"])
        return lead

    User = get_user_model()
    assigned_at = timezone.now()
    lead.assigned_branch = branch

    # First preference: active spa manager directly assigned to the branch.
    user = User.objects.filter(
        role="spa_manager",
        branch=branch,
        is_active=True,
    ).order_by("created_at").first()

    # Second preference: active area manager whose area_branches include it.
    if not user:
        user = User.objects.filter(
            role="area_manager",
            area_branches=branch,
            is_active=True,
        ).order_by("created_at").first()

    if user:
        lead.assigned_user = user
        lead.assigned_device = None
    else:
        # Final fallback: active registered device at the matched branch.
        lead.assigned_device = Device.objects.filter(
            branch=branch,
            is_active=True,
            is_blocked=False,
        ).order_by("-is_registered", "created_at").first()

    lead.status = DoubleTickLead.Status.ASSIGNED if (lead.assigned_user or lead.assigned_device) else DoubleTickLead.Status.UNASSIGNED
    lead.assigned_at = assigned_at if lead.status == DoubleTickLead.Status.ASSIGNED else None
    lead.save(update_fields=[
        "assigned_branch",
        "assigned_user",
        "assigned_device",
        "status",
        "assigned_at",
        "updated_at",
    ])
    return lead
