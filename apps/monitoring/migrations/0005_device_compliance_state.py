from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("devices", "0004_lastsynchistory"),
        ("monitoring", "0004_deviceevent_possible_uninstall"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeviceComplianceState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("status", models.CharField(choices=[("OK", "OK"), ("MISSING_ANDROID_ID", "Missing Android ID"), ("MISSING_FCM_TOKEN", "Missing FCM Token"), ("OUTDATED_APP", "Outdated App"), ("HEARTBEAT_MISSING", "Heartbeat Missing"), ("SUSPECTED_UNINSTALLED", "Suspected Uninstalled"), ("AUTH_BROKEN", "Auth Broken")], db_index=True, default="OK", max_length=40)),
                ("reason", models.TextField(blank=True)),
                ("fcm_invalid", models.BooleanField(db_index=True, default=False)),
                ("last_phone_notification_at", models.DateTimeField(blank=True, null=True)),
                ("last_admin_alert_at", models.DateTimeField(blank=True, null=True)),
                ("last_admin_email_at", models.DateTimeField(blank=True, null=True)),
                ("followed_up_at", models.DateTimeField(blank=True, null=True)),
                ("device", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="compliance_state", to="devices.device")),
            ],
            options={
                "db_table": "device_compliance_states",
                "indexes": [
                    models.Index(fields=["status", "updated_at"], name="device_comp_status__idx"),
                    models.Index(fields=["fcm_invalid"], name="device_comp_fcm_inv_idx"),
                ],
            },
        ),
    ]
