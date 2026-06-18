import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def merge_duplicate_visibilities(apps, schema_editor):
    visibility_model = apps.get_model("doubletick", "DoubleTickLeadVisibility")
    groups = {}
    queryset = visibility_model.objects.order_by("created_at", "id")
    for visibility in queryset:
        key = (visibility.lead_id, visibility.branch_id, visibility.user_id, visibility.device_id)
        groups.setdefault(key, []).append(visibility)

    for duplicates in groups.values():
        if len(duplicates) < 2:
            continue
        keep = duplicates[0]
        merged_notification_sent = keep.notification_sent or any(item.notification_sent for item in duplicates[1:])
        notification_dates = [item.notified_at for item in duplicates if item.notified_at]
        merged_notified_at = max(notification_dates) if notification_dates else keep.notified_at
        errors = [item.notification_error for item in duplicates if item.notification_error]
        keep.notification_sent = merged_notification_sent
        keep.notified_at = merged_notified_at
        keep.notification_error = keep.notification_error or (errors[0] if errors else "")
        keep.save(update_fields=["notification_sent", "notified_at", "notification_error", "updated_at"])
        visibility_model.objects.filter(id__in=[item.id for item in duplicates[1:]]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("doubletick", "0005_alter_doubletickmessage_options"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(merge_duplicate_visibilities, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="doubletickleadvisibility",
            constraint=models.UniqueConstraint(
                condition=models.Q(device__isnull=True, user__isnull=True),
                fields=("lead", "branch"),
                name="unique_dt_branch_visibility",
            ),
        ),
        migrations.AddConstraint(
            model_name="doubletickleadvisibility",
            constraint=models.UniqueConstraint(
                condition=models.Q(device__isnull=True, user__isnull=False),
                fields=("lead", "branch", "user"),
                name="unique_dt_user_visibility",
            ),
        ),
        migrations.AddConstraint(
            model_name="doubletickleadvisibility",
            constraint=models.UniqueConstraint(
                condition=models.Q(device__isnull=False, user__isnull=True),
                fields=("lead", "branch", "device"),
                name="unique_dt_device_visibility",
            ),
        ),
        migrations.CreateModel(
            name="DoubleTickDistributionAudit",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("success", "Success"), ("partial", "Partial"), ("failed", "Failed")], db_index=True, max_length=20)),
                ("mapped_branch_count", models.PositiveIntegerField(default=0)),
                ("visibility_count", models.PositiveIntegerField(default=0)),
                ("notification_success_count", models.PositiveIntegerField(default=0)),
                ("notification_failure_count", models.PositiveIntegerField(default=0)),
                ("failure_reason", models.TextField(blank=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "conversation",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="distribution_audits",
                        to="doubletick.doubletickconversation",
                    ),
                ),
                (
                    "lead",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="distribution_audits",
                        to="doubletick.doubleticklead",
                    ),
                ),
                (
                    "matched_area",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="distribution_audits",
                        to="doubletick.doubletickleadarea",
                    ),
                ),
            ],
            options={
                "db_table": "doubletick_distribution_audits",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["lead", "created_at"], name="dt_dist_audit_lead_idx"),
                    models.Index(fields=["status", "created_at"], name="dt_dist_audit_status_idx"),
                    models.Index(fields=["matched_area", "created_at"], name="dt_dist_audit_area_idx"),
                ],
            },
        ),
    ]
