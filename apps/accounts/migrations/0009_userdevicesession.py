from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0008_user_area_branches"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserDeviceSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("device_id", models.CharField(blank=True, db_index=True, default="", max_length=255)),
                ("device_name", models.CharField(blank=True, default="", max_length=255)),
                ("platform", models.CharField(blank=True, default="", max_length=50)),
                ("manufacturer", models.CharField(blank=True, default="", max_length=120)),
                ("model", models.CharField(blank=True, default="", max_length=120)),
                ("android_version", models.CharField(blank=True, default="", max_length=50)),
                ("app_version", models.CharField(blank=True, default="", max_length=50)),
                ("refresh_token_hash", models.CharField(db_index=True, max_length=64)),
                ("access_token_hash", models.CharField(blank=True, db_index=True, default="", max_length=64)),
                ("fcm_token", models.TextField(blank=True, default="")),
                ("ip", models.GenericIPAddressField(blank=True, null=True)),
                ("last_login", models.DateTimeField(blank=True, null=True)),
                ("last_activity", models.DateTimeField(blank=True, null=True)),
                ("last_refresh", models.DateTimeField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Active"), ("revoked", "Revoked"), ("expired", "Expired")],
                        db_index=True,
                        default="active",
                        max_length=20,
                    ),
                ),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="device_sessions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "user_device_sessions",
                "indexes": [
                    models.Index(fields=["user", "is_active", "status"], name="user_session_active_idx"),
                    models.Index(fields=["refresh_token_hash"], name="user_session_refresh_idx"),
                    models.Index(fields=["device_id", "user"], name="user_session_device_idx"),
                ],
            },
        ),
    ]
