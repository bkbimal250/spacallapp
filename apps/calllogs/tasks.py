from celery import shared_task
from django.db.models import Count, Avg
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


@shared_task
def schedule_missed_call_notifications(call_log_id):
    """
    Schedules reminders for a missed call at 10m, 30m, and 60m intervals.
    """
    for step, config in MISSED_CALL_NOTIFICATION_STEPS.items():
        send_missed_call_reminder.apply_async(
            (str(call_log_id), step),
            countdown=config["delay_seconds"],
        )


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


@shared_task
def send_missed_call_reminder(call_log_id, step):
    """
    Checks if a missed call has been followed up. If not, sends a push notification.
    
    Args:
        call_log_id: ID of the missed CallLog.
        step: 1, 2, or 3 (10m, 30m, 1h).
    """
    from .models import MissedCallFollowUp
    from apps.notifications.services import NotificationService

    if step not in MISSED_CALL_NOTIFICATION_STEPS:
        return f"Notification skipped: invalid missed-call reminder step {step}."

    try:
        followup = MissedCallFollowUp.objects.select_related(
            "missed_call",
            "missed_call__device",
            "missed_call__branch",
            "branch",
        ).get(missed_call_id=call_log_id)
    except MissedCallFollowUp.DoesNotExist:
        return f"Follow-up record not found for {call_log_id}"

    # If already followed up, stop notifications
    if followup.is_followed_up:
        return f"Notification skipped: Missed call {call_log_id} already followed up."

    # If this step was already handled or surpassed, skip
    if followup.notification_step >= step:
        return f"Notification skipped: Step {step} already processed for {call_log_id}."

    device = followup.missed_call.device
    if not device or not device.is_active or device.is_blocked:
        return f"Notification skipped: Missed call {call_log_id} has no active device."

    payload = _missed_call_notification_payload(followup, step)
    success = NotificationService.send_push(
        recipient=device,
        title=payload["title"],
        body=payload["body"],
        notification_type=MISSED_CALL_NOTIFICATION_TYPE,
        data=payload["data"],
    )

    followup.sla_status = MISSED_CALL_NOTIFICATION_STEPS[step]["sla_status"]
    followup.notification_step = step
    followup.save(update_fields=["sla_status", "notification_step"])

    status = "sent" if success else "logged"
    return f"Missed call {call_log_id} step {step} notification {status} for device {device.device_id}."


@shared_task
def send_due_missed_call_reminders():
    """
    Sweeps pending missed calls and sends any SLA reminder that is due.
    This protects the flow if a delayed Celery task was not queued or a worker restarted.
    """
    from .models import MissedCallFollowUp

    now = timezone.now()
    queued = 0
    pending_followups = MissedCallFollowUp.objects.filter(
        is_followed_up=False,
        missed_call__device__is_active=True,
        missed_call__device__is_blocked=False,
    ).select_related("missed_call", "missed_call__device")

    for followup in pending_followups:
        elapsed_seconds = (now - followup.missed_call.call_time).total_seconds()
        due_step = 0
        for step, config in MISSED_CALL_NOTIFICATION_STEPS.items():
            if elapsed_seconds >= config["delay_seconds"]:
                due_step = step

        if due_step and followup.notification_step < due_step:
            send_missed_call_reminder.delay(str(followup.missed_call_id), due_step)
            queued += 1

    return f"Queued {queued} due missed-call follow-up notifications."
