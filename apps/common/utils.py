"""
Shared utility functions used across the CallLog SPA Management System.

Provides role-based branch filtering helpers to avoid repeating the
same 3-role logic in every view.
"""


def get_branch_filter_ids(user):
    """
    Return a list of branch UUIDs (as strings) that the given user is
    allowed to see, based on their role.

    Rules:
        super_admin  → None (empty list) means "see everything, no filter"
        admin        → None (empty list) means "see everything, no filter"
        area_manager → assigned area_branches, else ['NONE']
        spa_manager  → [user.branch.id] if branch is assigned, else ['NONE']

    Returns:
        list[str] : Branch IDs to filter by.
                   Empty list [] = no restriction (admin/super_admin).
                   ['NONE']      = spa_manager with no branch (should see nothing).
    """
    if user.role in ["super_admin", "admin"]:
        # Admins see all branches — return empty list to indicate no filter
        return []

    if user.role == "spa_manager":
        if user.branch:
            # SPA managers see only their one assigned branch
            return [str(user.branch.id)]
        else:
            # SPA manager with no assigned branch → should see nothing
            # Return a placeholder that won't match any real branch
            return ["NONE"]

    if user.role == "area_manager":
        branch_ids = list(user.area_branches.values_list("id", flat=True))
        if branch_ids:
            return [str(branch_id) for branch_id in branch_ids]
        return ["NONE"]

    # Future-proof: any other role sees nothing
    return ["NONE"]


def apply_branch_filter(queryset, field_path, user, extra_branch_id=None):
    """
    Apply branch-based filtering to a queryset based on the user's role.

    Args:
        queryset       : The base Django queryset to filter.
        field_path     : The queryset field path to filter on (e.g. 'branch_id', 'device__branch_id').
        user           : The authenticated request.user object.
        extra_branch_id: An additional branch_id from query params (used for admin-side filtering).

    Returns:
        Filtered queryset.
    """
    branch_ids = get_branch_filter_ids(user)

    if branch_ids:
        # This user is restricted to specific branches
        queryset = queryset.filter(**{f"{field_path}__in": branch_ids})
    elif extra_branch_id:
        # Admin is applying a manual branch filter via query param
        if extra_branch_id == "null":
            queryset = queryset.filter(**{f"{field_path}__isnull": True})
        elif extra_branch_id.strip() and extra_branch_id not in ("undefined", ""):
            queryset = queryset.filter(**{field_path: extra_branch_id})

    return queryset
