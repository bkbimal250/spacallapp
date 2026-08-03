from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("branches", "0005_add_location_fk_fields_to_branch"),
    ]

    operations = [
        migrations.CreateModel(
            name="DashboardStatistic",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("date", models.DateField(db_index=True)),
                ("incoming", models.PositiveIntegerField(default=0)),
                ("outgoing", models.PositiveIntegerField(default=0)),
                ("missed", models.PositiveIntegerField(default=0)),
                ("total_calls", models.PositiveIntegerField(default=0)),
                ("active_devices", models.PositiveIntegerField(default=0)),
                ("total_devices", models.PositiveIntegerField(default=0)),
                ("total_contacts", models.PositiveIntegerField(default=0)),
                ("total_users", models.PositiveIntegerField(default=0)),
                ("total_leads", models.PositiveIntegerField(default=0)),
                ("total_exports", models.PositiveIntegerField(default=0)),
                ("avg_duration", models.FloatField(default=0.0)),
                ("conversion_rate", models.FloatField(default=0.0)),
                (
                    "branch",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dashboard_statistics",
                        to="branches.branch",
                    ),
                ),
            ],
            options={
                "db_table": "dashboard_statistics",
                "indexes": [
                    models.Index(fields=["date", "branch"], name="dash_stat_date_branch_idx"),
                    models.Index(fields=["branch", "-date"], name="dash_stat_branch_date_desc_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(fields=["branch", "date"], name="uniq_dashboard_stat_branch_date"),
                ],
            },
        ),
    ]
