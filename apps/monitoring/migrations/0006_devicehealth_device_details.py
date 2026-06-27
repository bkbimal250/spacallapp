from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("monitoring", "0005_device_compliance_state"),
    ]

    operations = [
        migrations.AddField(
            model_name="devicehealth",
            name="device_model",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="devicehealth",
            name="manufacturer",
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
        migrations.AddField(
            model_name="devicehealth",
            name="device_reported_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
