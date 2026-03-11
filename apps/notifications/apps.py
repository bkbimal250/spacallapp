from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'
    verbose_name = 'Push Notifications'

    def ready(self):
        """
        Initialize Firebase Admin SDK on application startup.
        """
        from .services import NotificationService
        NotificationService._initialize_firebase()
