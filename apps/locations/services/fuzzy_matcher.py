import time

from rapidfuzz import fuzz, process

from apps.branches.models import Branch
from apps.locations.models import (
    Area,
    AreaAlias,
    City,
    CityAlias,
    LocationGroup,
    LocationMatchIgnorePhrase,
    State,
    normalize_location_name,
)


CACHE_TTL = 30
AUTO_APPLY_SCORE = 92
SUGGESTION_SCORE = 80

_CANDIDATES_CACHE = None
_IGNORE_CACHE = None
_CACHE_EXPIRY = 0

_BUILT_IN_IGNORES = {
    "hi",
    "hy",
    "he",
    "hello",
    "namaste",
    "नमस्ते",
    "ok",
    "yes",
    "no",
    "hmm",
    "more info",
    "details",
    "price",
    "call me",
    "hindi me message kijiye",
    "hindi mein message kijiye",
    "job chahiye",
    "kaam chahiye",
    "काम चाहिए",
    "explore services",
}


def clear_location_candidate_cache(*args, **kwargs):
    global _CANDIDATES_CACHE, _IGNORE_CACHE, _CACHE_EXPIRY
    _CANDIDATES_CACHE = None
    _IGNORE_CACHE = None
    _CACHE_EXPIRY = 0


def _candidate(**values):
    values["text"] = normalize_location_name(values.get("text") or values.get("name"))
    return values


def build_location_candidates():
    """Load all lightweight matching choices in a few bulk queries."""
    global _CANDIDATES_CACHE, _IGNORE_CACHE, _CACHE_EXPIRY
    now = time.monotonic()
    if _CANDIDATES_CACHE is not None and now < _CACHE_EXPIRY:
        return _CANDIDATES_CACHE

    candidates = []
    for row in State.objects.filter(is_deleted=False, is_active=True).values(
        "id", "name", "normalized_name"
    ):
        candidates.append(_candidate(id=row["id"], name=row["name"], text=row["normalized_name"], type="state"))

    for row in City.objects.filter(is_deleted=False, is_active=True).values(
        "id", "name", "normalized_name", "state_id", "state__name"
    ):
        candidates.append(_candidate(
            id=row["id"], name=row["name"], text=row["normalized_name"], type="city",
            city_id=row["id"], city_name=row["name"], state_name=row["state__name"],
        ))

    for row in CityAlias.objects.filter(is_deleted=False, is_active=True).values(
        "id", "alias", "normalized_alias", "city_id", "city__name", "city__state__name"
    ):
        candidates.append(_candidate(
            id=row["id"], name=row["alias"], text=row["normalized_alias"], type="city_alias",
            city_id=row["city_id"], city_name=row["city__name"], state_name=row["city__state__name"],
        ))

    for row in LocationGroup.objects.filter(is_deleted=False, is_active=True).values(
        "id", "name", "normalized_name", "city_id", "city__name", "city__state__name"
    ):
        candidates.append(_candidate(
            id=row["id"], name=row["name"], text=row["normalized_name"], type="location_group",
            city_id=row["city_id"], city_name=row["city__name"], state_name=row["city__state__name"],
        ))

    for row in Area.objects.filter(is_deleted=False, is_active=True).values(
        "id", "name", "normalized_name", "city_id", "city__name", "city__state__name"
    ):
        candidates.append(_candidate(
            id=row["id"], name=row["name"], text=row["normalized_name"], type="area",
            area_id=row["id"], city_id=row["city_id"], city_name=row["city__name"],
            state_name=row["city__state__name"],
        ))

    for row in AreaAlias.objects.filter(is_deleted=False, is_active=True).values(
        "id", "alias", "normalized_alias", "area_id", "area__name",
        "area__city_id", "area__city__name", "area__city__state__name"
    ):
        candidates.append(_candidate(
            id=row["id"], name=row["alias"], text=row["normalized_alias"], type="area_alias",
            area_id=row["area_id"], area_name=row["area__name"], city_id=row["area__city_id"],
            city_name=row["area__city__name"], state_name=row["area__city__state__name"],
        ))

    for row in Branch.objects.filter(is_deleted=False, is_active=True).values(
        "id", "spa_name", "city", "area", "location_city_id", "location_area_id"
    ):
        candidates.append(_candidate(
            id=row["id"], name=row["spa_name"], type="branch", city_name=row["city"],
            area_name=row["area"], location_city_id=row["location_city_id"],
            location_area_id=row["location_area_id"],
        ))

    # Existing manually approved DoubleTick aliases are training examples.
    try:
        from apps.doubletick.models import DoubleTickAreaAlias, DoubleTickLeadArea

        for row in DoubleTickLeadArea.objects.filter(
            is_active=True, is_deleted=False
        ).values("id", "name", "normalized_name", "city"):
            candidates.append(_candidate(
                id=row["id"], name=row["name"], text=row["normalized_name"],
                type="doubletick_area", lead_area_id=row["id"],
                area_name=row["name"], city_name=row["city"],
            ))

        for row in DoubleTickAreaAlias.objects.filter(
            is_active=True, lead_area__is_active=True, lead_area__is_deleted=False
        ).values(
            "id", "alias", "normalized_alias", "lead_area_id",
            "lead_area__name", "lead_area__city", "channel_id"
        ):
            candidates.append(_candidate(
                id=row["id"], name=row["alias"], text=row["normalized_alias"],
                type="doubletick_area_alias", lead_area_id=row["lead_area_id"],
                area_name=row["lead_area__name"], city_name=row["lead_area__city"],
                channel_id=row["channel_id"],
            ))
    except (ImportError, LookupError):
        pass

    _IGNORE_CACHE = {
        normalize_location_name(value) for value in _BUILT_IN_IGNORES
    } | set(
        LocationMatchIgnorePhrase.objects.filter(
            is_deleted=False, is_active=True
        ).values_list("normalized_phrase", flat=True)
    )
    _CANDIDATES_CACHE = [item for item in candidates if item["text"]]
    _CACHE_EXPIRY = now + CACHE_TTL
    return _CANDIDATES_CACHE


def _context_candidates(candidates, context):
    if not context:
        return candidates
    if isinstance(context, dict):
        city = context.get("city") or context.get("raw_city")
        channel_id = context.get("channel_id")
    else:
        city, channel_id = context, None
    normalized_city = normalize_location_name(city)

    filtered = []
    for item in candidates:
        if channel_id and item.get("channel_id") and str(item["channel_id"]) != str(channel_id):
            continue
        candidate_city = normalize_location_name(item.get("city_name"))
        if normalized_city and candidate_city and candidate_city != normalized_city:
            continue
        filtered.append(item)
    return filtered or candidates


def _match(text, candidates, context=None):
    normalized = normalize_location_name(text)
    if not normalized or len(normalized) < 3:
        return None
    build_location_candidates()
    if normalized in (_IGNORE_CACHE or set()):
        return None

    candidates = _context_candidates(candidates, context)
    exact = [item for item in candidates if item["text"] == normalized]
    if exact:
        priority = {
            "doubletick_area_alias": 0, "area_alias": 1, "area": 2, "doubletick_area": 3,
            "branch": 4, "location_group": 5, "city_alias": 6, "city": 7, "state": 8,
        }
        exact.sort(key=lambda item: priority.get(item["type"], 99))
        return {"candidate": exact[0], "score": 100.0, "method": "exact"}

    choices = [item["text"] for item in candidates]
    if not choices:
        return None
    matched = process.extractOne(normalized, choices, scorer=fuzz.WRatio, score_cutoff=SUGGESTION_SCORE)
    if not matched:
        return None
    _, score, index = matched
    return {"candidate": candidates[index], "score": float(score), "method": "fuzzy"}


def fuzzy_match_location(text, context=None):
    return _match(text, build_location_candidates(), context=context)


def fuzzy_match_branch(text, context=None):
    branches = [item for item in build_location_candidates() if item["type"] == "branch"]
    return _match(text, branches, context=context)
