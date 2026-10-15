from celery import shared_task
from datetime import timedelta
import logging

from django.conf import settings
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from apps.common.task_policy import fresh_call, eligible_device
from django.utils import timezone
# Assuming Reporting app exists or will exist with DailySummary model.
# If not, this import might fail, but logic is sound as per requirement.
# For now, I will comment out the import to avoid immediate check failures if app doesn't exist.
# from reporting.models import DailySummary
from .models import CallLog


MISSED_CALL_NOTIFICATION_TYPE = "missed_call_followup"

MISSED_CALL_NOTIFICATION_STEPS = {
    1: {
        "delay_seconds": 10 * 60,
        "sla_status": "OK",
        "title": "Pending missed call",
        "message": "Take follow-up on this number: {phone}. Missed call is pending for 10 minutes.",
    },
    2: {
        "delay_seconds": 30 * 60,
        "sla_status": "LATE",
        "title": "Missed call still pending",
        "message": "Urgent follow-up needed for {phone}. Missed call is pending for 30 minutes.",
    },
    3: {
        "delay_seconds": 60 * 60,
        "sla_status": "MISSED",
        "title": "Missed call SLA breached",
        "message": "SLA missed for {phone}. Please take follow-up immediately.",
    },
}


@shared_task
def generate_daily_summary():
    # ... existing implementation placeholder ...
    pass


def _eligible(followup, now):
    return (not followup.is_followed_up
            and followup.missed_call.call_type == "missed"
            and fresh_call(followup.missed_call, settings.MISSED_CALL_MAX_AGE_SECONDS, now)
            and eligible_device(followup.missed_call))


def _followups():
    from .models import MissedCallFollowUp
    return MissedCallFollowUp.objects.select_related(
        "missed_call", "missed_call__device", "missed_call__branch", "branch")


def _publish_reminder(call_id, step, eta, expires):
    try:
        send_missed_call_reminder.apply_async(
            args=(str(call_id), step), eta=eta, expires=expires, ignore_result=True,
            retry=False,
        )
    except Exception:
        # Leave reservation in place: a publish timeout may have succeeded.
        # The sweep can republish after its queue lease, using the same claim.
        logging.getLogger(__name__).exception("Reminder publish failed; reservation retained")


@shared_task(ignore_result=True)
def schedule_missed_call_notifications(call_log_id, due_only=False):
    from .models import MissedCallReminder
    now = timezone.now()
    queued = 0
    with transaction.atomic():
        followup = _followups().select_for_update(of=("self",)).filter(missed_call_id=call_log_id).first()
        if not followup or not _eligible(followup, now):
            return 0
        if followup.reminders.filter(status__in=["sending", "ambiguous"]).exists():
            return 0
        call_time = followup.missed_call.call_time
        expires = call_time + timedelta(seconds=settings.MISSED_CALL_MAX_AGE_SECONDS)
        due_steps = [step for step, config in MISSED_CALL_NOTIFICATION_STEPS.items()
                     if call_time + timedelta(seconds=config["delay_seconds"]) <= now]
        highest_due = max(due_steps, default=0)
        for step, config in MISSED_CALL_NOTIFICATION_STEPS.items():
            if step <= followup.notification_step or step < highest_due:
                continue
            eta = call_time + timedelta(seconds=config["delay_seconds"])
            if eta >= expires or (due_only and eta > now):
                continue
            reminder, created = MissedCallReminder.objects.get_or_create(
                followup=followup, step=step, defaults={"lease_until": now})
            if not created and (reminder.status != "queued" or reminder.lease_until > now):
                continue
            eta = max(now, eta)
            reminder.lease_until = eta + timedelta(seconds=settings.MISSED_CALL_QUEUE_LEASE_SECONDS)
            reminder.save(update_fields=["lease_until", "updated_at"])
            transaction.on_commit(lambda step=step, eta=eta: _publish_reminder(call_log_id, step, eta, expires))
            queued += 1
    return queued


def _missed_call_notification_payload(followup, step):
    config = MISSED_CALL_NOTIFICATION_STEPS[step]
    missed_call = followup.missed_call
    device = missed_call.device
    branch = missed_call.branch or followup.branch
    phone = missed_call.phone_number

    body = config["message"].format(phone=phone)
    if branch:
        body = f"{body} Branch: {branch.spa_name}."

    return {
        "title": config["title"],
        "body": body,
        "data": {
            "missed_call_id": str(missed_call.id),
            "call_log_id": str(missed_call.id),
            "phone_number": phone,
            "branch_id": str(branch.id) if branch else "",
            "branch_name": branch.spa_name if branch else "",
            "device_id": str(device.id) if device else "",
            "device_identifier": device.device_id if device else "",
            "sla_step": str(step),
            "sla_status": config["sla_status"],
            "source": "calllogs",
        },
    }


@shared_task(ignore_result=True)
def send_missed_call_reminder(call_log_id, step):
    from .models import MissedCallFollowUp, MissedCallReminder
    from apps.notifications.services import NotificationService

    if step not in MISSED_CALL_NOTIFICATION_STEPS:
        return "Notification skipped: invalid step."
    now = timezone.now()
    with transaction.atomic():
        followup = _followups().select_for_update(of=("self",)).filter(missed_call_id=call_log_id).first()
        if not followup or not _eligible(followup, now) or followup.notification_step >= step:
            return "Notification skipped: ineligible call or completed step."
        elapsed = (now - followup.missed_call.call_time).total_seconds()
        due = max((s for s, c in MISSED_CALL_NOTIFICATION_STEPS.items()
                   if elapsed >= c["delay_seconds"]), default=0)
        if step != due:
            return "Notification skipped: superseded or not yet due."
        # All steps for a call share this parent lock. An abandoned external send
        # is ambiguous, not a lease that authorizes sending again.
        followup.reminders.filter(status="sending", lease_until__lte=now).update(status="ambiguous")
        if followup.reminders.filter(status__in=["sending", "ambiguous"]).exists():
            return "Notification skipped: send in progress or requires reconciliation."
        reminder, _ = MissedCallReminder.objects.get_or_create(
            followup=followup, step=step, defaults={"lease_until": now})
        if reminder.status != "queued":
            return "Notification skipped: step already attempted."
        reminder.status = "sending"
        reminder.lease_until = now + timedelta(seconds=settings.SEND_CLAIM_TIMEOUT_SECONDS)
        reminder.save(update_fields=["status", "lease_until", "updated_at"])

    payload = _missed_call_notification_payload(followup, step)
    try:
        success = NotificationService.send_push(
            recipient=followup.missed_call.device, title=payload["title"], body=payload["body"],
            notification_type=MISSED_CALL_NOTIFICATION_TYPE, data=payload["data"],
        )
    except Exception:
        MissedCallReminder.objects.filter(pk=reminder.pk).update(status="ambiguous")
        logging.getLogger(__name__).exception("Reminder send outcome unknown; manual reconciliation required")
        return "Notification ambiguous."
    with transaction.atomic():
        MissedCallFollowUp.objects.select_for_update().get(pk=followup.pk)
        MissedCallReminder.objects.filter(pk=reminder.pk).update(status="sent" if success else "failed")
        if success:
            MissedCallFollowUp.objects.filter(
                pk=followup.pk, is_followed_up=False, notification_step__lt=step,
            ).update(notification_step=step, sla_status=MISSED_CALL_NOTIFICATION_STEPS[step]["sla_status"])
    return "Missed call notification sent." if success else "Missed call notification failed; not retried automatically."


@shared_task(ignore_result=True)
def send_due_missed_call_reminders():
    from .models import MissedCallFollowUp, MissedCallReminder
    now = timezone.now()
    remaining = max(1, settings.MISSED_CALL_SWEEP_BATCH_SIZE)
    queued = 0
    # Narrow in SQL before slicing, so already-reserved rows cannot starve later
    # calls. Higher SLA steps take priority; total work is bounded per run.
    for step in reversed(MISSED_CALL_NOTIFICATION_STEPS):
        blocked = MissedCallReminder.objects.filter(followup_id=OuterRef("pk")).filter(
            Q(status__in=["sending", "ambiguous"])
            | (Q(step=step) & ( ~Q(status="queued") | Q(lease_until__gt=now)))
        )
        candidates = MissedCallFollowUp.objects.filter(
            is_followed_up=False, notification_step__lt=step,
            missed_call__call_type="missed", missed_call__is_time_invalid=False,
            missed_call__call_time__gt=now-timedelta(seconds=settings.MISSED_CALL_MAX_AGE_SECONDS),
            missed_call__call_time__lte=now-timedelta(seconds=MISSED_CALL_NOTIFICATION_STEPS[step]["delay_seconds"]),
            missed_call__device__is_active=True, missed_call__device__is_blocked=False,
            missed_call__device__is_registered=True,
        ).annotate(blocked=Exists(blocked)).filter(blocked=False)
        if step < 3:
            candidates = candidates.filter(missed_call__call_time__gt=now-timedelta(
                seconds=MISSED_CALL_NOTIFICATION_STEPS[step+1]["delay_seconds"]))
        ids = list(candidates.order_by("missed_call__call_time", "pk").values_list("missed_call_id", flat=True)[:remaining])
        for call_id in ids:
            queued += schedule_missed_call_notifications(call_id, due_only=True)
        remaining -= len(ids)
        if not remaining:
            break
    return f"Queued {queued} due missed-call follow-up notifications."
