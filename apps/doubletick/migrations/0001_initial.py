# Generated manually because the local Python runtime is unavailable in this workspace.

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("branches", "0004_alter_branch_spa_name"),
        ("devices", "0004_lastsynchistory"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DoubleTickLead",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("customer_name", models.CharField(blank=True, max_length=255)),
                ("whatsapp_name", models.CharField(blank=True, max_length=255)),
                ("phone_number", models.CharField(db_index=True, max_length=30)),
                ("normalized_phone", models.CharField(blank=True, db_index=True, max_length=15)),
                ("message", models.TextField(blank=True)),
                ("city", models.CharField(blank=True, max_length=100)),
                ("area", models.CharField(blank=True, max_length=100)),
                ("service_name", models.CharField(blank=True, max_length=255)),
                ("source_ad", models.CharField(blank=True, max_length=255)),
                ("doubletick_customer_id", models.CharField(blank=True, max_length=255)),
                ("doubletick_chat_id", models.CharField(blank=True, max_length=255)),
                ("doubletick_message_id", models.CharField(blank=True, max_length=255)),
                ("raw_payload", models.JSONField(blank=True, default=dict)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("new", "New"),
                            ("assigned", "Assigned"),
                            ("opened", "Opened"),
                            ("contacted", "Contacted"),
                            ("follow_up", "Follow Up"),
                            ("booked", "Booked"),
                            ("lost", "Lost"),
                            ("unassigned", "Unassigned"),
                            ("failed", "Failed"),
                        ],
                        db_index=True,
                        default="new",
                        max_length=20,
                    ),
                ),
                ("assigned_at", models.DateTimeField(blank=True, null=True)),
                ("opened_at", models.DateTimeField(blank=True, null=True)),
                ("contacted_at", models.DateTimeField(blank=True, null=True)),
                ("follow_up_at", models.DateTimeField(blank=True, null=True)),
                ("booked_at", models.DateTimeField(blank=True, null=True)),
                ("lost_reason", models.TextField(blank=True)),
                ("is_duplicate", models.BooleanField(db_index=True, default=False)),
                (
                    "assigned_branch",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="doubletick_leads",
                        to="branches.branch",
                    ),
                ),
                (
                    "assigned_device",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="doubletick_leads",
                        to="devices.device",
                    ),
                ),
                (
                    "assigned_user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="doubletick_leads",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "duplicate_of",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="duplicates",
                        to="doubletick.doubleticklead",
                    ),
                ),
            ],
            options={
                "db_table": "doubletick_leads",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="DoubleTickWebhookLog",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("event_type", models.CharField(blank=True, max_length=100)),
                ("doubletick_event_id", models.CharField(blank=True, max_length=255, null=True)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("processed", models.BooleanField(db_index=True, default=False)),
                ("error_message", models.TextField(blank=True, null=True)),
                (
                    "lead",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="webhook_logs",
                        to="doubletick.doubleticklead",
                    ),
                ),
            ],
            options={
                "db_table": "doubletick_webhook_logs",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="DoubleTickLeadActivity",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("created", "Created"),
                            ("assigned", "Assigned"),
                            ("opened", "Opened"),
                            ("contacted", "Contacted"),
                            ("follow_up", "Follow Up"),
                            ("booked", "Booked"),
                            ("lost", "Lost"),
                            ("reassigned", "Reassigned"),
                            ("failed", "Failed"),
                            ("note", "Note"),
                        ],
                        db_index=True,
                        max_length=20,
                    ),
                ),
                ("note", models.TextField(blank=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "device",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="doubletick_activities",
                        to="devices.device",
                    ),
                ),
                (
                    "lead",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="activities",
                        to="doubletick.doubleticklead",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="doubletick_activities",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "doubletick_lead_activities",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="doubleticklead",
            index=models.Index(fields=["phone_number"], name="dt_lead_phone_idx"),
        ),
        migrations.AddIndex(
            model_name="doubleticklead",
            index=models.Index(fields=["normalized_phone"], name="dt_lead_norm_phone_idx"),
        ),
        migrations.AddIndex(
            model_name="doubleticklead",
            index=models.Index(fields=["city", "area"], name="dt_lead_city_area_idx"),
        ),
        migrations.AddIndex(
            model_name="doubleticklead",
            index=models.Index(fields=["status"], name="dt_lead_status_idx"),
        ),
        migrations.AddIndex(
            model_name="doubleticklead",
            index=models.Index(fields=["assigned_branch"], name="dt_lead_branch_idx"),
        ),
        migrations.AddIndex(
            model_name="doubleticklead",
            index=models.Index(fields=["assigned_user"], name="dt_lead_user_idx"),
        ),
        migrations.AddIndex(
            model_name="doubleticklead",
            index=models.Index(fields=["created_at"], name="dt_lead_created_idx"),
        ),
        migrations.AddIndex(
            model_name="doubletickleadactivity",
            index=models.Index(fields=["lead", "created_at"], name="dt_activity_lead_created_idx"),
        ),
        migrations.AddIndex(
            model_name="doubletickleadactivity",
            index=models.Index(fields=["action"], name="dt_activity_action_idx"),
        ),
        migrations.AddIndex(
            model_name="doubletickwebhooklog",
            index=models.Index(fields=["event_type"], name="dt_webhook_event_idx"),
        ),
        migrations.AddIndex(
            model_name="doubletickwebhooklog",
            index=models.Index(fields=["doubletick_event_id"], name="dt_webhook_event_id_idx"),
        ),
        migrations.AddIndex(
            model_name="doubletickwebhooklog",
            index=models.Index(fields=["processed"], name="dt_webhook_processed_idx"),
        ),
    ]
