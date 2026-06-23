# apps/locations/views.py

from uuid import UUID

from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.db.models import Prefetch
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import (
    AreaAliasFilter,
    AreaFilter,
    BranchCoverageAreaFilter,
    CityAliasFilter,
    CityFilter,
    LocationGroupAreaFilter,
    LocationGroupFilter,
    LocationMatchIgnorePhraseFilter,
    StateFilter,
)
from .models import (
    Area,
    AreaAlias,
    BranchCoverageArea,
    City,
    CityAlias,
    LocationGroup,
    LocationGroupArea,
    LocationMatchIgnorePhrase,
    State,
    normalize_location_name,
)
from .serializers import (
    AreaAliasSerializer,
    AreaAliasListSerializer,
    AreaMiniSerializer,
    AreaListSerializer,
    AreaSerializer,
    BranchCoverageAreaSerializer,
    CityAliasSerializer,
    CityAliasListSerializer,
    CityMiniSerializer,
    CityListSerializer,
    CitySerializer,
    LocationAnalyticsSerializer,
    LocationGroupAreaSerializer,
    LocationGroupAreaListSerializer,
    LocationGroupMiniSerializer,
    LocationGroupListSerializer,
    LocationGroupSerializer,
    LocationMatchIgnorePhraseSerializer,
    LocationMatchRequestSerializer,
    StateListSerializer,
    StateMiniSerializer,
    StateSerializer,
)


class SoftDeleteModelViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    compact_serializer_class = None

    def is_compact_list_request(self):
        compact = str(self.request.query_params.get("compact", "")).lower() in {"1", "true", "yes"}
        return getattr(self, "action", None) == "list" and compact

    def get_serializer_class(self):
        if self.is_compact_list_request() and self.compact_serializer_class:
            return self.compact_serializer_class
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(queryset.model, "is_deleted"):
            queryset = queryset.filter(is_deleted=False)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if str(request.query_params.get("all", "")).lower() in {"1", "true", "yes"}:
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        if hasattr(instance, "is_deleted"):
            instance.is_deleted = True
            instance.save(update_fields=["is_deleted", "updated_at"])
        else:
            instance.delete()

    def perform_create(self, serializer):
        try:
            serializer.save()
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {
                    "detail": "This record already exists. Refresh the list to view the existing record.",
                    "constraint": str(exc),
                }
            ) from exc

    def perform_update(self, serializer):
        try:
            serializer.save()
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {
                    "detail": "This update conflicts with an existing record.",
                    "constraint": str(exc),
                }
            ) from exc


class StateViewSet(SoftDeleteModelViewSet):
    queryset = State.objects.all()
    serializer_class = StateSerializer
    compact_serializer_class = StateListSerializer
    filterset_class = StateFilter
    search_fields = ["name", "normalized_name", "code"]
    ordering_fields = ["name", "priority", "created_at"]
    ordering = ["priority", "name"]

    def get_queryset(self):
        return super().get_queryset().annotate(
            city_count_cached=Count("cities", filter=Q(cities__is_deleted=False), distinct=True),
            area_count_cached=Count("cities__areas", filter=Q(cities__areas__is_deleted=False), distinct=True),
            group_count_cached=Count(
                "cities__location_groups",
                filter=Q(cities__location_groups__is_deleted=False),
                distinct=True,
            ),
            branch_coverage_count_cached=Count(
                "cities__areas__branch_coverages",
                filter=Q(cities__areas__branch_coverages__is_deleted=False, cities__areas__branch_coverages__is_active=True),
                distinct=True,
            ),
        )

    @action(detail=False, methods=["get"])
    def options(self, request):
        qs = self.filter_queryset(self.get_queryset().filter(is_active=True)).only("id", "name", "is_active")
        return Response(StateMiniSerializer(qs, many=True).data)


class CityViewSet(SoftDeleteModelViewSet):
    queryset = City.objects.select_related("state")
    serializer_class = CitySerializer
    compact_serializer_class = CityListSerializer
    filterset_class = CityFilter
    search_fields = ["name", "normalized_name", "aliases__alias"]
    ordering_fields = ["name", "priority", "created_at"]
    ordering = ["state__name", "priority", "name"]

    def get_queryset(self):
        return super().get_queryset().annotate(
            area_count_cached=Count("areas", filter=Q(areas__is_deleted=False), distinct=True),
            group_count_cached=Count("location_groups", filter=Q(location_groups__is_deleted=False), distinct=True),
            alias_count_cached=Count("aliases", filter=Q(aliases__is_deleted=False), distinct=True),
            branch_coverage_count_cached=Count(
                "areas__branch_coverages",
                filter=Q(areas__branch_coverages__is_deleted=False, areas__branch_coverages__is_active=True),
                distinct=True,
            ),
        )

    @action(detail=False, methods=["get"])
    def options(self, request):
        qs = self.filter_queryset(self.get_queryset().filter(is_active=True)).only(
            "id",
            "state_id",
            "name",
            "is_active",
            "state__name",
        )
        return Response(CityMiniSerializer(qs, many=True).data)


class CityAliasViewSet(SoftDeleteModelViewSet):
    queryset = CityAlias.objects.select_related("city", "city__state")
    serializer_class = CityAliasSerializer
    compact_serializer_class = CityAliasListSerializer
    filterset_class = CityAliasFilter
    search_fields = ["alias", "normalized_alias", "city__name"]
    ordering_fields = ["alias", "created_at"]
    ordering = ["city__name", "alias"]


class AreaViewSet(SoftDeleteModelViewSet):
    queryset = Area.objects.select_related("city", "city__state")
    serializer_class = AreaSerializer
    compact_serializer_class = AreaListSerializer
    filterset_class = AreaFilter
    search_fields = ["name", "normalized_name", "aliases__alias"]
    ordering_fields = ["name", "priority", "created_at"]
    ordering = ["city__name", "priority", "name"]

    def get_queryset(self):
        return super().get_queryset().annotate(
            alias_count_cached=Count("aliases", filter=Q(aliases__is_deleted=False), distinct=True),
            group_count_cached=Count("area_groups", filter=Q(area_groups__is_deleted=False), distinct=True),
            branch_coverage_count_cached=Count(
                "branch_coverages",
                filter=Q(branch_coverages__is_deleted=False, branch_coverages__is_active=True),
                distinct=True,
            ),
        )

    @action(detail=False, methods=["get"])
    def options(self, request):
        qs = self.filter_queryset(self.get_queryset().filter(is_active=True)).only(
            "id",
            "city_id",
            "name",
            "is_active",
            "city__name",
            "city__state__name",
        )
        return Response(AreaMiniSerializer(qs, many=True).data)


class AreaAliasViewSet(SoftDeleteModelViewSet):
    queryset = AreaAlias.objects.select_related("area", "area__city", "area__city__state")
    serializer_class = AreaAliasSerializer
    compact_serializer_class = AreaAliasListSerializer
    filterset_class = AreaAliasFilter
    search_fields = ["alias", "normalized_alias", "area__name"]
    ordering_fields = ["alias", "created_at"]
    ordering = ["area__city__name", "area__name", "alias"]


class LocationGroupViewSet(SoftDeleteModelViewSet):
    queryset = LocationGroup.objects.select_related("city", "city__state")
    serializer_class = LocationGroupSerializer
    compact_serializer_class = LocationGroupListSerializer
    filterset_class = LocationGroupFilter
    search_fields = ["name", "normalized_name", "description"]
    ordering_fields = ["name", "priority", "created_at"]
    ordering = ["city__name", "priority", "name"]

    def get_queryset(self):
        queryset = super().get_queryset().annotate(
            area_count_cached=Count("group_areas", filter=Q(group_areas__is_deleted=False), distinct=True),
            branch_coverage_count_cached=Count(
                "branch_coverages",
                filter=Q(branch_coverages__is_deleted=False, branch_coverages__is_active=True),
                distinct=True,
            ),
        )
        if getattr(self, "action", None) == "retrieve":
            active_group_areas = LocationGroupArea.objects.select_related(
                "area",
                "area__city",
            ).filter(is_deleted=False)
            return queryset.prefetch_related(Prefetch("group_areas", queryset=active_group_areas))
        return queryset

    @action(detail=False, methods=["get"])
    def options(self, request):
        qs = self.filter_queryset(self.get_queryset().filter(is_active=True)).only(
            "id",
            "city_id",
            "name",
            "is_active",
            "city__name",
            "city__state__name",
        )
        return Response(LocationGroupMiniSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="sync-areas")
    def sync_areas(self, request, pk=None):
        group = self.get_object()
        area_ids = request.data.get("area_ids", [])
        if not isinstance(area_ids, list):
            raise serializers.ValidationError({"area_ids": "Expected a list of area ids."})

        unique_area_ids = []
        seen = set()
        for area_id in area_ids:
            value = str(area_id)
            try:
                UUID(value)
            except ValueError as exc:
                raise serializers.ValidationError({"area_ids": f"Invalid area id: {value}"}) from exc
            if value not in seen:
                unique_area_ids.append(value)
                seen.add(value)

        areas = list(Area.objects.filter(id__in=unique_area_ids, is_deleted=False))
        found_ids = {str(area.id) for area in areas}
        missing_ids = [area_id for area_id in unique_area_ids if area_id not in found_ids]
        if missing_ids:
            raise serializers.ValidationError({"area_ids": f"Invalid area ids: {', '.join(missing_ids)}"})

        wrong_city = [area.name for area in areas if area.city_id != group.city_id]
        if wrong_city:
            raise serializers.ValidationError({
                "area_ids": "Selected areas must belong to the same city as the location group.",
                "invalid_areas": wrong_city,
            })

        with transaction.atomic():
            selected_ids = {str(area.id) for area in areas}
            LocationGroupArea.objects.filter(group=group, is_deleted=False).exclude(area_id__in=selected_ids).update(is_deleted=True)

            for index, area in enumerate(areas):
                mapping = LocationGroupArea.objects.filter(group=group, area=area).first()
                if mapping:
                    updates = []
                    if mapping.is_deleted:
                        mapping.is_deleted = False
                        updates.append("is_deleted")
                    if mapping.priority != index:
                        mapping.priority = index
                        updates.append("priority")
                    if updates:
                        mapping.save(update_fields=updates + ["updated_at"])
                else:
                    LocationGroupArea.objects.create(group=group, area=area, priority=index)

        refreshed = self.get_queryset().get(pk=group.pk)
        return Response(self.get_serializer(refreshed).data, status=status.HTTP_200_OK)


class LocationGroupAreaViewSet(SoftDeleteModelViewSet):
    queryset = LocationGroupArea.objects.select_related(
        "group",
        "group__city",
        "area",
        "area__city",
    )
    serializer_class = LocationGroupAreaSerializer
    compact_serializer_class = LocationGroupAreaListSerializer
    filterset_class = LocationGroupAreaFilter
    ordering_fields = ["priority", "created_at"]
    ordering = ["group__name", "priority", "area__name"]


class BranchCoverageAreaViewSet(SoftDeleteModelViewSet):
    queryset = BranchCoverageArea.objects.select_related(
        "content_type",
        "area",
        "area__city",
        "area__city__state",
        "location_group",
    )
    serializer_class = BranchCoverageAreaSerializer
    filterset_class = BranchCoverageAreaFilter
    search_fields = ["object_id", "area__name", "area__city__name", "notes"]
    ordering_fields = ["priority", "created_at"]
    ordering = ["priority", "area__city__name", "area__name"]


class LocationMatchIgnorePhraseViewSet(SoftDeleteModelViewSet):
    queryset = LocationMatchIgnorePhrase.objects.all()
    serializer_class = LocationMatchIgnorePhraseSerializer
    filterset_class = LocationMatchIgnorePhraseFilter
    search_fields = ["phrase", "normalized_phrase"]
    ordering_fields = ["phrase", "phrase_type", "created_at"]
    ordering = ["phrase_type", "phrase"]


class LocationMatchAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LocationMatchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        text = serializer.validated_data["text"]
        normalized_text = normalize_location_name(text)

        city_id = serializer.validated_data.get("city_id")
        state_id = serializer.validated_data.get("state_id")
        group_id = serializer.validated_data.get("group_id")

        result = self.match_text(
            text=text,
            normalized_text=normalized_text,
            state_id=state_id,
            city_id=city_id,
            group_id=group_id,
        )

        return Response(result, status=status.HTTP_200_OK)

    def match_text(self, text, normalized_text, state_id=None, city_id=None, group_id=None):
        exact_ignore = LocationMatchIgnorePhrase.objects.filter(
            is_deleted=False,
            is_active=True,
            normalized_phrase=normalized_text,
        ).first()

        if exact_ignore:
            return {
                "classification": exact_ignore.phrase_type,
                "confidence": 1.0,
                "reason": "Matched ignore phrase. This is not a location.",
                "normalized_text": normalized_text,
                "raw_text": text,
                "state": None,
                "city": None,
                "group": None,
                "area": None,
                "branch": None,
            }

        # Structured bot payload support.
        # Example: city:<uuid>, group:<uuid>, area:<uuid>, action:explore_services
        if ":" in normalized_text:
            prefix, value = normalized_text.split(":", 1)
            prefix = prefix.strip()
            value = value.strip()

            if prefix == "action":
                return {
                    "classification": "action",
                    "confidence": 1.0,
                    "reason": "Structured action payload.",
                    "normalized_text": normalized_text,
                    "raw_text": text,
                    "raw_service": value,
                }

        # Branch style text: PALM ATLANTIS - BELAPUR
        if "-" in text:
            left, right = [part.strip() for part in text.split("-", 1)]
            area_match = self.find_area(normalize_location_name(right), city_id=city_id)
            if area_match:
                return {
                    "classification": "branch",
                    "confidence": 0.88,
                    "reason": "Detected branch name with area after hyphen.",
                    "normalized_text": normalized_text,
                    "raw_text": text,
                    "raw_branch": left,
                    "raw_area": right,
                    "area": AreaMiniSerializer(area_match).data,
                    "city": CityMiniSerializer(area_match.city).data,
                    "state": StateMiniSerializer(area_match.city.state).data,
                    "branch": {"name": left},
                }

        # Area exact/alias match.
        area = self.find_area(normalized_text, city_id=city_id, group_id=group_id)
        if area:
            return {
                "classification": "area",
                "confidence": 0.95,
                "reason": "Matched area name or alias.",
                "normalized_text": normalized_text,
                "raw_text": text,
                "raw_area": text,
                "area": AreaMiniSerializer(area).data,
                "city": CityMiniSerializer(area.city).data,
                "state": StateMiniSerializer(area.city.state).data,
            }

        # Group exact match.
        group = self.find_group(normalized_text, city_id=city_id)
        if group:
            return {
                "classification": "location_group",
                "confidence": 0.92,
                "reason": "Matched location group.",
                "normalized_text": normalized_text,
                "raw_text": text,
                "raw_group": text,
                "group": LocationGroupMiniSerializer(group).data,
                "city": CityMiniSerializer(group.city).data,
                "state": StateMiniSerializer(group.city.state).data,
            }

        # City exact/alias match.
        city = self.find_city(normalized_text, state_id=state_id)
        if city:
            return {
                "classification": "city",
                "confidence": 0.95,
                "reason": "Matched city name or alias.",
                "normalized_text": normalized_text,
                "raw_text": text,
                "raw_city": text,
                "city": CityMiniSerializer(city).data,
                "state": StateMiniSerializer(city.state).data,
            }

        # State exact match.
        state = State.objects.filter(
            is_deleted=False,
            is_active=True,
            normalized_name=normalized_text,
        ).first()

        if state:
            return {
                "classification": "state",
                "confidence": 0.95,
                "reason": "Matched state name.",
                "normalized_text": normalized_text,
                "raw_text": text,
                "state": StateMiniSerializer(state).data,
            }

        return {
            "classification": "unknown",
            "confidence": 0.0,
            "reason": "No confident location match.",
            "normalized_text": normalized_text,
            "raw_text": text,
            "state": None,
            "city": None,
            "group": None,
            "area": None,
            "branch": None,
        }

    def find_city(self, normalized_text, state_id=None):
        qs = City.objects.filter(is_deleted=False, is_active=True)

        if state_id:
            qs = qs.filter(state_id=state_id)

        city = qs.filter(normalized_name=normalized_text).first()
        if city:
            return city

        alias = CityAlias.objects.filter(
            is_deleted=False,
            is_active=True,
            normalized_alias=normalized_text,
        )

        if state_id:
            alias = alias.filter(city__state_id=state_id)

        alias = alias.select_related("city", "city__state").first()
        return alias.city if alias else None

    def find_group(self, normalized_text, city_id=None):
        qs = LocationGroup.objects.filter(is_deleted=False, is_active=True)

        if city_id:
            qs = qs.filter(city_id=city_id)

        return qs.filter(normalized_name=normalized_text).select_related("city", "city__state").first()

    def find_area(self, normalized_text, city_id=None, group_id=None):
        qs = Area.objects.filter(is_deleted=False, is_active=True)

        if city_id:
            qs = qs.filter(city_id=city_id)

        if group_id:
            qs = qs.filter(area_groups__group_id=group_id, area_groups__is_deleted=False)

        area = qs.filter(normalized_name=normalized_text).select_related("city", "city__state").first()
        if area:
            return area

        alias = AreaAlias.objects.filter(
            is_deleted=False,
            is_active=True,
            normalized_alias=normalized_text,
        )

        if city_id:
            alias = alias.filter(area__city_id=city_id)

        if group_id:
            alias = alias.filter(
                area__area_groups__group_id=group_id,
                area__area_groups__is_deleted=False,
            )

        alias = alias.select_related("area", "area__city", "area__city__state").first()
        return alias.area if alias else None


class LocationAnalyticsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = {
            "states": self.entity_stats(State),
            "cities": self.entity_stats(City),
            "areas": self.entity_stats(Area),
            "groups": self.entity_stats(LocationGroup),
            "city_aliases": self.entity_stats(CityAlias),
            "area_aliases": self.entity_stats(AreaAlias),
            "branch_coverages": self.entity_stats(BranchCoverageArea),
            "ignore_phrases": self.entity_stats(LocationMatchIgnorePhrase),
            "top_states": self.top_states(),
            "top_cities": self.top_cities(),
            "top_areas": self.top_areas(),
            "suspicious": self.suspicious_stats(),
        }

        serializer = LocationAnalyticsSerializer(data)
        return Response(serializer.data)

    def entity_stats(self, model):
        qs = model.objects.all()
        total = qs.filter(is_deleted=False).count()
        active = qs.filter(is_deleted=False, is_active=True).count() if hasattr(model, "is_active") else total
        inactive = total - active
        deleted = qs.filter(is_deleted=True).count()

        return {
            "total": total,
            "active": active,
            "inactive": inactive,
            "deleted": deleted,
        }

    def top_states(self):
        qs = State.objects.filter(is_deleted=False).annotate(
            city_count=Count("cities", filter=Q(cities__is_deleted=False), distinct=True),
            area_count=Count("cities__areas", filter=Q(cities__areas__is_deleted=False), distinct=True),
            group_count=Count(
                "cities__location_groups",
                filter=Q(cities__location_groups__is_deleted=False),
                distinct=True,
            ),
            branch_coverage_count=Count(
                "cities__areas__branch_coverages",
                filter=Q(cities__areas__branch_coverages__is_deleted=False),
                distinct=True,
            ),
        ).order_by("-branch_coverage_count", "-area_count")[:10]

        return [
            {
                "id": str(item.id),
                "name": item.name,
                "code": item.code,
                "city_count": item.city_count,
                "area_count": item.area_count,
                "group_count": item.group_count,
                "branch_coverage_count": item.branch_coverage_count,
            }
            for item in qs
        ]

    def top_cities(self):
        qs = City.objects.filter(is_deleted=False).select_related("state").annotate(
            area_count=Count("areas", filter=Q(areas__is_deleted=False), distinct=True),
            group_count=Count("location_groups", filter=Q(location_groups__is_deleted=False), distinct=True),
            alias_count=Count("aliases", filter=Q(aliases__is_deleted=False), distinct=True),
            branch_coverage_count=Count(
                "areas__branch_coverages",
                filter=Q(areas__branch_coverages__is_deleted=False),
                distinct=True,
            ),
        ).order_by("-branch_coverage_count", "-area_count")[:10]

        return [
            {
                "id": str(item.id),
                "name": item.name,
                "state_name": item.state.name,
                "area_count": item.area_count,
                "group_count": item.group_count,
                "alias_count": item.alias_count,
                "branch_coverage_count": item.branch_coverage_count,
            }
            for item in qs
        ]

    def top_areas(self):
        qs = Area.objects.filter(is_deleted=False).select_related("city", "city__state").annotate(
            alias_count=Count("aliases", filter=Q(aliases__is_deleted=False), distinct=True),
            group_count=Count("area_groups", filter=Q(area_groups__is_deleted=False), distinct=True),
            branch_coverage_count=Count(
                "branch_coverages",
                filter=Q(branch_coverages__is_deleted=False),
                distinct=True,
            ),
        ).order_by("-branch_coverage_count")[:10]

        return [
            {
                "id": str(item.id),
                "name": item.name,
                "city_name": item.city.name,
                "state_name": item.city.state.name,
                "alias_count": item.alias_count,
                "group_count": item.group_count,
                "branch_coverage_count": item.branch_coverage_count,
            }
            for item in qs
        ]

    def suspicious_stats(self):
        city_names = list(
            City.objects.filter(is_deleted=False).values_list("normalized_name", flat=True)
        )

        area_same_as_city = Area.objects.filter(
            is_deleted=False,
            normalized_name__in=city_names,
        ).count()

        groups_without_areas = LocationGroup.objects.filter(
            is_deleted=False,
        ).annotate(
            c=Count("group_areas", filter=Q(group_areas__is_deleted=False))
        ).filter(c=0).count()

        branches_without_group = BranchCoverageArea.objects.filter(
            is_deleted=False,
            is_active=True,
            location_group__isnull=True,
        ).count()

        return {
            "areas_same_as_city_name": area_same_as_city,
            "groups_without_areas": groups_without_areas,
            "active_branch_coverages_without_group": branches_without_group,
        }
