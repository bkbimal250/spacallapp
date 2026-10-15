"""Manual/startup preflight. Prints no broker URLs, credentials, or task payloads."""
import os


def main():
    import django
    django.setup()
    from django.conf import settings
    from config import celery_app
    celery_app.autodiscover_tasks(force=True)
    queue = settings.CELERY_TASK_DEFAULT_QUEUE
    if queue == "celery" or os.environ.get("CELERY_TASK_DEFAULT_QUEUE") != queue:
        raise RuntimeError("Worker environment queue must match the non-legacy application queue")
    if set(celery_app.amqp.queues) != {queue}:
        raise RuntimeError("Unexpected declared worker queues")
    for name in celery_app.tasks:
        if name.startswith("apps."):
            task = celery_app.tasks[name]
            routed = celery_app.amqp.router.route({}, name)
            if task.app is not celery_app or routed["queue"].name != queue:
                raise RuntimeError("Project task binding/route mismatch")
    if celery_app.conf.worker_eta_task_limit != 100:
        raise RuntimeError("Expected bounded ETA task configuration")
    print("CallLog task binding, queue ownership, and ETA limit verified; no tasks published.")


if __name__ == "__main__":
    main()
