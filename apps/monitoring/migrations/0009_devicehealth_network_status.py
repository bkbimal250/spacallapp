from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("monitoring", "0008_devicehealth_pending_sync_details"),
    ]

    operations = [
        migrations.AddField(
            model_name="devicehealth",
            name="network_type",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
        migrations.AddField(
            model_name="devicehealth",
            name="is_metered",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="devicehealth",
            name="is_data_saver_on",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="devicehealth",
            name="is_background_restricted",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="devicehealth",
            name="is_battery_optimized",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="devicehealth",
            name="is_vpn_active",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="devicehealth",
            name="is_proxy_configured",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="devicehealth",
            name="is_airplane_mode_on",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="devicehealth",
            name="last_network_error",
            field=models.TextField(blank=True, default=""),
        ),
    ]
