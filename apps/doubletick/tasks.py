"""
Celery task placeholder for DoubleTick.

No background task is required for the first phase because webhook processing is
kept synchronous: save log, create/assign lead, then send notification through
the existing NotificationService.
"""
