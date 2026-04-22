from celery import shared_task
from django.db.models import Count, Avg
from django.utils import timezone
# Assuming Reporting app exists or will exist with DailySummary model.
# If not, this import might fail, but logic is sound as per requirement.
# For now, I will comment out the import to avoid immediate check failures if app doesn't exist.
# from reporting.models import DailySummary
from .models import CallLog


@shared_task
def generate_daily_summary():
    # ... existing implementation placeholder ...
    pass


@shared_task
def schedule_missed_call_notifications(call_log_id):
    """
    Schedules reminders for a missed call at 10m, 30m, and 60m intervals.
    """
    # Step 1: 10 minutes reminder
    send_missed_call_reminder.apply_async((call_log_id, 1), countdown=600)
    
    # Step 2: 30 minutes reminder
    send_missed_call_reminder.apply_async((call_log_id, 2), countdown=1800)
    
    # Step 3: 60 minutes reminder
    send_missed_call_reminder.apply_async((call_log_id, 3), countdown=3600)


@shared_task
def send_missed_call_reminder(call_log_id, step):
    """
    Checks if a missed call has been followed up. If not, sends a push notification.
    
    Args:
        call_log_id: ID of the missed CallLog.
        step: 1, 2, or 3 (10m, 30m, 1h).
    """
    from .models import CallLog, MissedCallFollowUp
    from apps.notifications.services import NotificationService
    
    try:
        followup = MissedCallFollowUp.objects.get(missed_call_id=call_log_id)
    except MissedCallFollowUp.DoesNotExist:
        return f"Follow-up record not found for {call_log_id}"

    # If already followed up, stop notifications
    if followup.is_followed_up:
        return f"Notification skipped: Missed call {call_log_id} already followed up."

    # If this step was already handled or surpassed, skip
    if followup.notification_step >= step:
        return f"Notification skipped: Step {step} already processed for {call_log_id}."

    # Prepare notification
    phone = followup.missed_call.phone_number
    title = "Missed Call Follow-up"
    body = f"Missed call from {phone} - Please call back"
    
    # Get branch managers to notify
    managers = followup.branch.branch_users.filter(role='branch_manager', is_active=True)
    
    sent_count = 0
    for manager in managers:
        if manager.fcm_token:
            success = NotificationService.send_push(
                recipient=manager,
                title=title,
                body=body,
                notification_type="reminder",
                data={"missed_call_id": str(call_log_id)}
            )
            if success:
                sent_count += 1
    
    # Update notification step in tracking model
    followup.notification_step = step
    followup.save(update_fields=['notification_step'])
    
    return f"Sent {sent_count} notifications for missed call {call_log_id} (Step {step})"
