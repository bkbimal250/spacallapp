from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("monitoring", "0007_device_time_wrong"),
    ]

    operations = [
        migrations.AddField(
            model_name="devicehealth",
            name="last_sync_error",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="devicehealth",
            name="pending_call_count",
            field=models.IntegerField(default=0),
        ),
    ]
