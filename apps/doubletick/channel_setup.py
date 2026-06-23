import re

from django.db.models import Q

from apps.branches.models import BranchGroups

from .models import DoubleTickChannel


DEFAULT_DOUBLETICK_CHANNELS = [
    {
        "name": "Spa Advisor Main",
        "waba_number": "917506359139",
        "state": "",
        "city": "",
        "branch_group": "Main",
    },
    {
        "name": "Spa Advisor Main 800",
        "waba_number": "918976822800",
        "state": "All India",
        "city": "",
        "branch_group": "Main",
    },
    {
        "name": "Spa Advisor Rajasthan",
        "waba_number": "918976822801",
        "state": "Rajasthan",
        "city": "",
        "branch_group": "Rajasthan",
    },
    {
        "name": "Spa Advisor Gujarat",
        "waba_number": "918976822802",
        "state": "Gujarat",
        "city": "",
        "branch_group": "Gujarat",
    },
    {
        "name": "Spa Advisor Bangalore",
        "waba_number": "918976822803",
        "state": "Karnataka",
        "city": "Bangalore",
        "branch_group": "Bangalore",
    },
]


def normalize_waba_number(value):
    return re.sub(r"\D", "", str(value or ""))


def branch_group_for_name(name, create=False):
    clean_name = str(name or "").strip()
    if not clean_name:
        return None
    group = BranchGroups.objects.filter(name__iexact=clean_name, is_deleted=False).first()
    if group or not create:
        return group
    return BranchGroups.objects.create(name=clean_name, is_active=True)


def setup_default_channels(dry_run=False, only_missing=False):
    stats = {"created": 0, "updated": 0, "skipped": 0}
    actions = []
    for config in DEFAULT_DOUBLETICK_CHANNELS:
        waba_number = normalize_waba_number(config["waba_number"])
        channel = DoubleTickChannel.objects.filter(waba_number=waba_number).first()
        if channel and only_missing:
            stats["skipped"] += 1
            actions.append(("skipped", waba_number, "already exists"))
            continue

        branch_group = branch_group_for_name(config["branch_group"], create=not dry_run)
        desired = {
            "name": config["name"],
            "waba_number": waba_number,
            "state": config["state"],
            "city": config["city"],
            "branch_group": branch_group,
            "is_active": True,
        }

        if channel:
            changes = {}
            if channel.branch_group_id != getattr(branch_group, "id", None):
                changes["branch_group"] = branch_group
            changes.update({
                field: value
                for field, value in desired.items()
                if field != "branch_group" and getattr(channel, field) != value
            })
            if changes:
                stats["updated"] += 1
                actions.append(("updated", waba_number, ", ".join(changes.keys())))
                if not dry_run:
                    for field, value in changes.items():
                        setattr(channel, field, value)
                    channel.save(update_fields=list(changes.keys()) + ["updated_at"])
            else:
                stats["skipped"] += 1
                actions.append(("skipped", waba_number, "already up to date"))
        else:
            stats["created"] += 1
            actions.append(("created", waba_number, config["name"]))
            if not dry_run:
                DoubleTickChannel.objects.create(**desired)
    return stats, actions


def find_channel_for_waba_number(value, active_only=True):
    digits = normalize_waba_number(value)
    if not digits:
        return None
    queryset = DoubleTickChannel.objects.all()
    if active_only:
        queryset = queryset.filter(is_active=True)
    channel = queryset.filter(Q(waba_number=digits) | Q(waba_number=f"+{digits}")).first()
    if channel:
        return channel
    for candidate in queryset.only("id", "waba_number"):
        if normalize_waba_number(candidate.waba_number) == digits:
            return candidate
    return None
