from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("monitoring", "0003_monitoring_realtime_event_types"),
    ]

    operations = [
        migrations.AlterField(
            model_name="deviceevent",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("offline", "Device Offline"),
                    ("sim_change", "SIM Card Changed"),
                    ("sync_failure", "Sync Failure"),
                    ("battery_low", "Battery Low"),
                    ("storage_full", "Storage Full"),
                    ("network_weak", "Weak Network Signal"),
                    ("permission_denied", "Permission Denied"),
                    ("app_crash", "App Crash"),
                    ("app_uninstall_suspected", "Possible App Uninstall"),
                ],
                max_length=32,
            ),
        ),
    ]
