from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("calllogs", "0007_dashboard_performance_indexes")]
    operations = [
        migrations.CreateModel(
            name="MissedCallReminder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("step", models.PositiveSmallIntegerField()),
                ("status", models.CharField(max_length=16, default="queued", choices=[(v, v) for v in ("queued", "sending", "sent", "failed", "ambiguous", "skipped")])),
                ("lease_until", models.DateTimeField()),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("followup", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reminders", to="calllogs.missedcallfollowup")),
            ],
            options={"constraints": [models.UniqueConstraint(fields=("followup", "step"), name="unique_missed_reminder_step")]},
        ),
    ]
