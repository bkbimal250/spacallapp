from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("monitoring", "0006_devicehealth_device_details"),
    ]

    operations = [
        migrations.AddField(
            model_name="devicehealth",
            name="device_time_skew_seconds",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="devicecompliancestate",
            name="device_time_wrong",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name="devicecompliancestate",
            name="status",
            field=models.CharField(
                choices=[
                    ("OK", "OK"),
                    ("MISSING_ANDROID_ID", "Missing Android ID"),
                    ("MISSING_FCM_TOKEN", "Missing FCM Token"),
                    ("OUTDATED_APP", "Outdated App"),
                    ("HEARTBEAT_MISSING", "Heartbeat Missing"),
                    ("SUSPECTED_UNINSTALLED", "Suspected Uninstalled"),
                    ("AUTH_BROKEN", "Auth Broken"),
                    ("DEVICE_TIME_WRONG", "Device Time Wrong"),
                ],
                db_index=True,
                default="OK",
                max_length=40,
            ),
        ),
    ]
