from django.conf import settings


def route_project_task(name, args=None, kwargs=None, options=None, **extra):
    if name.startswith("apps.") or name == "config.celery.debug_task":
        return {"queue": settings.CELERY_TASK_DEFAULT_QUEUE}
