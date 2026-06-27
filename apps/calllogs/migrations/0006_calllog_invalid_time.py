from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("calllogs", "0005_auto_20260603_1729"),
    ]

    operations = [
        migrations.AddField(
            model_name="calllog",
            name="device_reported_call_time",
            field=models.DateTimeField(
                blank=True,
                help_text="Original device-reported call time when the server had to use a safe timestamp.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="calllog",
            name="invalid_time_reason",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="calllog",
            name="is_time_invalid",
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
