import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("doubletick", "0003_doubletickactivity_dt_activity_conv_created_idx_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="doubletickmessage",
            name="assigned_to_raw",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="doubletickmessage",
            name="message_timestamp",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="doubletickmessage",
            name="sender_display_name",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="doubletickmessage",
            name="sent_by_raw",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.CreateModel(
            name="DoubleTickTeamMemberMapping",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("doubletick_user_id", models.CharField(blank=True, db_index=True, max_length=255)),
                ("doubletick_phone", models.CharField(blank=True, db_index=True, max_length=30)),
                ("display_name", models.CharField(max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "channel",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="team_member_mappings",
                        to="doubletick.doubletickchannel",
                    ),
                ),
                (
                    "crm_user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="doubletick_team_mappings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "doubletick_team_member_mappings",
                "ordering": ["display_name"],
            },
        ),
        migrations.AddIndex(
            model_name="doubletickmessage",
            index=models.Index(fields=["status"], name="dt_msg_status_idx"),
        ),
        migrations.AddIndex(
            model_name="doubletickmessage",
            index=models.Index(fields=["message_timestamp"], name="dt_msg_timestamp_idx"),
        ),
        migrations.AddIndex(
            model_name="doubletickteammembermapping",
            index=models.Index(fields=["doubletick_user_id", "is_active"], name="dt_team_user_active_idx"),
        ),
        migrations.AddIndex(
            model_name="doubletickteammembermapping",
            index=models.Index(fields=["doubletick_phone", "is_active"], name="dt_team_phone_active_idx"),
        ),
    ]
