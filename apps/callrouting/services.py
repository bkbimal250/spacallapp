import logging
import re
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Max, Q
from django.utils import timezone

from apps.branches.models import Branch
from apps.branches.services import BranchOperatingHoursService
from apps.callrouting.models import (
    RoutingAttempt,
    RoutingCandidate,
    RoutingEvent,
    RoutingRequest,
    RoutingRule,
)
from apps.leadmanagement.models import LeadManagement
from apps.locations.models import BranchCoverageArea

logger = logging.getLogger(__name__)


TERMINAL_REQUEST_STATUSES = {
    RoutingRequest.Status.ROUTED,
    RoutingRequest.Status.SKIPPED,
    RoutingRequest.Status.FAILED,
}


class PhoneNormalizationService:
    """Normalize customer numbers for routing without changing CallLog storage."""

    @staticmethod
    def normalize(raw_phone):
        digits = re.sub(r"\D", "", str(raw_phone or ""))
        if len(digits) == 10:
            return f"+91{digits}"
        if len(digits) == 12 and digits.startswith("91"):
            return f"+91{digits[-10:]}"
        if len(digits) > 12 and digits.endswith(digits[-10:]):
            return f"+91{digits[-10:]}" if len(digits[-10:]) == 10 else ""
        return ""


class RoutingRuleService:
    """Resolve enabled routing rules for a call timestamp."""

    @staticmethod
    def _local_time(value):
        if value is None:
            value = timezone.now()
        if timezone.is_naive(value):
            value = timezone.make_aware(value, timezone.get_current_timezone())
        return timezone.localtime(value).time()

    @staticmethod
    def _window_matches(rule, at_datetime):
        if not rule.start_time or not rule.end_time:
            return True
        call_time = RoutingRuleService._local_time(at_datetime)
        if rule.start_time <= rule.end_time:
            return rule.start_time <= call_time < rule.end_time
        return call_time >= rule.start_time or call_time < rule.end_time

    @staticmethod
    def _active_window_matches(rule, at_datetime):
        if not at_datetime:
            at_datetime = timezone.now()
        if timezone.is_naive(at_datetime):
            at_datetime = timezone.make_aware(at_datetime, timezone.get_current_timezone())
        if rule.active_from and at_datetime < rule.active_from:
            return False
        if rule.active_until and at_datetime >= rule.active_until:
            return False
        return True

    @classmethod
    def resolve_rule(cls, at_datetime, routing_type=RoutingRule.RoutingType.NIGHT):
        rules = RoutingRule.objects.filter(enabled=True, routing_type=routing_type).order_by("priority", "created_at")
        for rule in rules:
            if cls._active_window_matches(rule, at_datetime) and cls._window_matches(rule, at_datetime):
                return rule
        return None


@dataclass(frozen=True)
class CandidateEvaluation:
    branch: Branch
    relevance_score: int
    is_open: bool
    is_eligible: bool
    rejection_reason: str


class CandidateSelectionService:
    """
    Discover and rank candidate branches using existing location data.

    Score is deterministic:
    same area = +400, same location group = +300, same city = +200,
    BranchCoverageArea match = +100. Ties use branch code/name/id.
    """

    SAME_AREA_SCORE = 400
    SAME_GROUP_SCORE = 300
    SAME_CITY_SCORE = 200
    COVERAGE_SCORE = 100

    @staticmethod
    def _coverage_branch_ids(source_branch):
        area_ids = set()
        if source_branch.location_area_id:
            area_ids.add(source_branch.location_area_id)

        branch_ct = ContentType.objects.get_for_model(Branch)
        source_coverage = BranchCoverageArea.objects.filter(
            content_type=branch_ct,
            object_id=str(source_branch.id),
            is_active=True,
            is_deleted=False,
        ).values_list("area_id", flat=True)
        area_ids.update(source_coverage)

        if not area_ids:
            return set()

        return set(
            BranchCoverageArea.objects.filter(
                content_type=branch_ct,
                area_id__in=area_ids,
                is_active=True,
                is_deleted=False,
            ).exclude(object_id=str(source_branch.id)).values_list("object_id", flat=True)
        )

    @classmethod
    def _base_queryset(cls, source_branch):
        location_q = Q()
        if source_branch.location_area_id:
            location_q |= Q(location_area_id=source_branch.location_area_id)
        elif source_branch.area:
            location_q |= Q(area__iexact=source_branch.area)

        if source_branch.location_group_id:
            location_q |= Q(location_group_id=source_branch.location_group_id)

        if source_branch.location_city_id:
            location_q |= Q(location_city_id=source_branch.location_city_id)
        elif source_branch.city:
            location_q |= Q(city__iexact=source_branch.city)

        coverage_ids = cls._coverage_branch_ids(source_branch)
        if coverage_ids:
            location_q |= Q(id__in=coverage_ids)

        if not location_q:
            return Branch.objects.none()

        return Branch.objects.filter(
            location_q,
            is_active=True,
            is_deleted=False,
        ).exclude(id=source_branch.id).select_related(
            "location_area",
            "location_group",
            "location_city",
        ).distinct()

    @classmethod
    def _score(cls, source_branch, candidate, coverage_ids):
        score = 0
        if source_branch.location_area_id and candidate.location_area_id == source_branch.location_area_id:
            score += cls.SAME_AREA_SCORE
        elif source_branch.area and candidate.area and candidate.area.lower() == source_branch.area.lower():
            score += cls.SAME_AREA_SCORE

        if source_branch.location_group_id and candidate.location_group_id == source_branch.location_group_id:
            score += cls.SAME_GROUP_SCORE

        if source_branch.location_city_id and candidate.location_city_id == source_branch.location_city_id:
            score += cls.SAME_CITY_SCORE
        elif source_branch.city and candidate.city and candidate.city.lower() == source_branch.city.lower():
            score += cls.SAME_CITY_SCORE

        if str(candidate.id) in coverage_ids:
            score += cls.COVERAGE_SCORE
        return score

    @classmethod
    def evaluate_candidates(cls, source_branch, at_datetime):
        if not source_branch:
            return []

        coverage_ids = cls._coverage_branch_ids(source_branch)
        evaluations = []
        for branch in cls._base_queryset(source_branch):
            score = cls._score(source_branch, branch, coverage_ids)
            is_open = BranchOperatingHoursService.is_branch_open(branch, at_datetime)
            evaluations.append(
                CandidateEvaluation(
                    branch=branch,
                    relevance_score=score,
                    is_open=is_open,
                    is_eligible=is_open and score > 0,
                    rejection_reason="" if is_open and score > 0 else "closed" if not is_open else "location_not_eligible",
                )
            )

        return sorted(
            evaluations,
            key=lambda item: (
                -int(item.is_eligible),
                -item.relevance_score,
                item.branch.code or "",
                item.branch.spa_name or "",
                str(item.branch.id),
            ),
        )


class RoutingService:
    """Synchronous routing decision engine. It does not send WhatsApp."""

    @staticmethod
    def _event(routing_request, event_type, message="", metadata=None):
        return RoutingEvent.objects.create(
            routing_request=routing_request,
            event_type=event_type,
            message=message,
            metadata=metadata or {},
        )

    @staticmethod
    def _next_attempt_number(routing_request):
        current = RoutingAttempt.objects.filter(routing_request=routing_request).aggregate(max_attempt=Max("attempt_number"))
        return (current["max_attempt"] or 0) + 1

    @staticmethod
    def _attach_call_log_snapshots(routing_request, call_log):
        updates = []
        values = {
            "source_branch": call_log.branch,
            "source_device": call_log.device,
            "contact": call_log.contact,
            "call_time": call_log.call_time,
        }
        for field, value in values.items():
            if getattr(routing_request, f"{field}_id", None) != getattr(value, "id", value):
                setattr(routing_request, field, value)
                updates.append(field)
        return updates

    @staticmethod
    def _resolve_lead(routing_request, call_log):
        if routing_request.lead_id:
            return []
        lead = LeadManagement.objects.filter(calllog=call_log).first()
        if not lead:
            return []
        routing_request.lead = lead
        return ["lead"]

    @staticmethod
    def _apply_terminal(routing_request, status, reason="", completed=True):
        routing_request.status = status
        routing_request.rejection_reason = reason
        if completed:
            routing_request.completed_at = timezone.now()

    @classmethod
    def _cooldown_blocked(cls, routing_request, rule, at_datetime):
        if not routing_request.normalized_phone or not rule.cooldown_minutes:
            return False
        cutoff = at_datetime - timedelta(minutes=rule.cooldown_minutes)
        return RoutingRequest.objects.filter(
            normalized_phone=routing_request.normalized_phone,
            routing_type=rule.routing_type,
            status=RoutingRequest.Status.ROUTED,
            call_time__gte=cutoff,
        ).exclude(id=routing_request.id).exists()

    @classmethod
    def process_call_log(cls, call_log, routing_type=RoutingRule.RoutingType.NIGHT):
        routing_request = None
        attempt = None
        try:
            with transaction.atomic():
                routing_request, _ = RoutingRequest.objects.select_for_update().get_or_create(
                    call_log=call_log,
                    defaults={
                        "source_branch": call_log.branch,
                        "source_device": call_log.device,
                        "contact": call_log.contact,
                        "call_time": call_log.call_time,
                        "routing_type": routing_type,
                    },
                )

                if routing_request.status in TERMINAL_REQUEST_STATUSES:
                    return routing_request

                attempt = RoutingAttempt.objects.create(
                    routing_request=routing_request,
                    attempt_number=cls._next_attempt_number(routing_request),
                    status=RoutingAttempt.Status.STARTED,
                    started_at=timezone.now(),
                )

                RoutingCandidate.objects.filter(routing_request=routing_request).delete()
                routing_request.events.all().delete()
                cls._event(routing_request, RoutingEvent.EventType.RECEIVED)

                update_fields = cls._attach_call_log_snapshots(routing_request, call_log)
                update_fields += cls._resolve_lead(routing_request, call_log)

                routing_request.status = RoutingRequest.Status.PROCESSING
                routing_request.routing_type = routing_type
                normalized_phone = PhoneNormalizationService.normalize(call_log.phone_number)
                routing_request.normalized_phone = normalized_phone
                update_fields.extend(["status", "routing_type", "normalized_phone"])

                if not normalized_phone:
                    cls._apply_terminal(
                        routing_request,
                        RoutingRequest.Status.SKIPPED,
                        RoutingRequest.RejectionReason.INVALID_PHONE,
                    )
                    routing_request.save()
                    cls._event(routing_request, RoutingEvent.EventType.INVALID_PHONE)
                    attempt.status = RoutingAttempt.Status.SUCCESS
                    attempt.completed_at = timezone.now()
                    attempt.save(update_fields=["status", "completed_at"])
                    return routing_request

                cls._event(routing_request, RoutingEvent.EventType.PHONE_VALIDATED)
                rule = RoutingRuleService.resolve_rule(call_log.call_time, routing_type=routing_type)
                if not rule:
                    cls._apply_terminal(
                        routing_request,
                        RoutingRequest.Status.SKIPPED,
                        RoutingRequest.RejectionReason.NO_RULE,
                    )
                    routing_request.routing_rule = None
                    routing_request.save()
                    cls._event(routing_request, RoutingEvent.EventType.NO_RULE)
                    attempt.status = RoutingAttempt.Status.SUCCESS
                    attempt.completed_at = timezone.now()
                    attempt.save(update_fields=["status", "completed_at"])
                    return routing_request

                routing_request.routing_rule = rule
                routing_request.routing_type = rule.routing_type
                cls._event(routing_request, RoutingEvent.EventType.RULE_MATCHED, metadata={"rule_id": str(rule.id)})

                if cls._cooldown_blocked(routing_request, rule, call_log.call_time):
                    cls._apply_terminal(
                        routing_request,
                        RoutingRequest.Status.SKIPPED,
                        RoutingRequest.RejectionReason.CUSTOMER_COOLDOWN,
                    )
                    routing_request.save()
                    cls._event(routing_request, RoutingEvent.EventType.COOLDOWN_BLOCKED)
                    attempt.status = RoutingAttempt.Status.SUCCESS
                    attempt.completed_at = timezone.now()
                    attempt.save(update_fields=["status", "completed_at"])
                    return routing_request

                source_open = BranchOperatingHoursService.is_branch_open(call_log.branch, call_log.call_time)
                routing_request.source_branch_open = source_open
                routing_request.source_open_checked_at = timezone.now()
                if source_open:
                    cls._apply_terminal(
                        routing_request,
                        RoutingRequest.Status.SKIPPED,
                        RoutingRequest.RejectionReason.SOURCE_SPA_OPEN,
                    )
                    routing_request.save()
                    cls._event(routing_request, RoutingEvent.EventType.SOURCE_SPA_OPEN)
                    attempt.status = RoutingAttempt.Status.SUCCESS
                    attempt.completed_at = timezone.now()
                    attempt.save(update_fields=["status", "completed_at"])
                    return routing_request

                cls._event(routing_request, RoutingEvent.EventType.SOURCE_SPA_CLOSED)
                evaluations = CandidateSelectionService.evaluate_candidates(call_log.branch, call_log.call_time)
                selected_count = 0
                eligible_count = 0
                candidates_to_create = []
                max_recommendations = rule.max_recommendations or 0
                for evaluation in evaluations:
                    is_selected = evaluation.is_eligible and selected_count < max_recommendations
                    rank = selected_count + 1 if is_selected else None
                    if evaluation.is_eligible:
                        eligible_count += 1
                    if is_selected:
                        selected_count += 1
                    candidates_to_create.append(
                        RoutingCandidate(
                            routing_request=routing_request,
                            branch=evaluation.branch,
                            rank=rank,
                            relevance_score=evaluation.relevance_score,
                            is_open=evaluation.is_open,
                            is_eligible=evaluation.is_eligible,
                            is_selected=is_selected,
                            rejection_reason=evaluation.rejection_reason,
                            evaluated_at=timezone.now(),
                        )
                    )

                if candidates_to_create:
                    RoutingCandidate.objects.bulk_create(candidates_to_create)

                if eligible_count:
                    cls._event(
                        routing_request,
                        RoutingEvent.EventType.CANDIDATES_FOUND,
                        metadata={"eligible_count": eligible_count, "selected_count": selected_count},
                    )
                if selected_count:
                    cls._event(
                        routing_request,
                        RoutingEvent.EventType.CANDIDATE_SELECTED,
                        metadata={"selected_count": selected_count},
                    )
                    cls._apply_terminal(routing_request, RoutingRequest.Status.ROUTED, "")
                else:
                    cls._event(routing_request, RoutingEvent.EventType.NO_CANDIDATE)
                    cls._apply_terminal(
                        routing_request,
                        RoutingRequest.Status.SKIPPED,
                        RoutingRequest.RejectionReason.NO_CANDIDATE,
                    )

                routing_request.save()
                attempt.status = RoutingAttempt.Status.SUCCESS
                attempt.completed_at = timezone.now()
                attempt.save(update_fields=["status", "completed_at"])
                return routing_request
        except Exception as exc:
            logger.exception("Call routing processing failed", extra={"call_log_id": str(getattr(call_log, "id", ""))})
            with transaction.atomic():
                routing_request, _ = RoutingRequest.objects.select_for_update().get_or_create(
                    call_log=call_log,
                    defaults={
                        "source_branch": call_log.branch,
                        "source_device": call_log.device,
                        "contact": call_log.contact,
                        "call_time": call_log.call_time,
                        "routing_type": routing_type,
                    },
                )
                routing_request.status = RoutingRequest.Status.FAILED
                routing_request.rejection_reason = RoutingRequest.RejectionReason.ERROR
                routing_request.completed_at = timezone.now()
                routing_request.metadata = {**routing_request.metadata, "error": str(exc)}
                routing_request.save(update_fields=["status", "rejection_reason", "completed_at", "metadata", "updated_at"])
                cls._event(routing_request, RoutingEvent.EventType.ERROR, message=str(exc))
                if attempt and RoutingAttempt.objects.filter(pk=attempt.pk).exists():
                    attempt.status = RoutingAttempt.Status.FAILED
                    attempt.completed_at = timezone.now()
                    attempt.error_code = exc.__class__.__name__
                    attempt.error_message = str(exc)
                    attempt.save(update_fields=["status", "completed_at", "error_code", "error_message"])
                else:
                    RoutingAttempt.objects.create(
                        routing_request=routing_request,
                        attempt_number=cls._next_attempt_number(routing_request),
                        status=RoutingAttempt.Status.FAILED,
                        started_at=timezone.now(),
                        completed_at=timezone.now(),
                        error_code=exc.__class__.__name__,
                        error_message=str(exc),
                    )
            return routing_request
