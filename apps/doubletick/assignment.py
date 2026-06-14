"""
Backward-compatible assignment helpers.

The current DoubleTick workflow distributes only confirmed area leads through
DoubleTickLeadAreaBranch mappings. These wrappers remain for older imports but
do not bypass the pending-conversation safeguards.
"""

from .models import DoubleTickLead, DoubleTickLeadAreaBranch


def find_matching_branch(city, area):
    """
    Return the first active branch manually mapped to a matching lead area.

    This intentionally does not trust Branch.area directly; area distribution is
    controlled by DoubleTickLeadArea and DoubleTickLeadAreaBranch.
    """
    mapping = DoubleTickLeadAreaBranch.objects.select_related("branch", "lead_area").filter(
        lead_area__name__iexact=area or "",
        lead_area__city__iexact=city or "",
        lead_area__is_active=True,
        branch__is_active=True,
        is_active=True,
        receives_leads=True,
    ).order_by("priority", "branch__spa_name").first()
    return mapping.branch if mapping else None


def assign_lead_to_user_or_device(lead):
    """
    Legacy no-bypass assignment wrapper.

    Qualified leads should be distributed via LeadDistributionService. If this
    helper is called for an unqualified lead, it leaves the lead unassigned.
    """
    if lead.status not in [DoubleTickLead.Status.QUALIFIED, DoubleTickLead.Status.AREA_MATCHED, DoubleTickLead.Status.AVAILABLE]:
        return lead

    from .services import LeadDistributionService

    if lead.matched_area_id:
        return LeadDistributionService.distribute(lead)
    lead.status = DoubleTickLead.Status.FAILED
    lead.save(update_fields=["status", "updated_at"])
    return lead
