from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("monitoring", "0010_dedupe_active_device_events"),
    ]

    operations = [
        migrations.CreateModel(
            name="APIRequestMetric",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("request_id", models.CharField(db_index=True, max_length=64)),
                ("method", models.CharField(max_length=12)),
                ("path", models.CharField(db_index=True, max_length=500)),
                ("view_name", models.CharField(blank=True, default="", max_length=255)),
                ("status_code", models.PositiveIntegerField(db_index=True)),
                ("duration_ms", models.FloatField(db_index=True)),
                ("sql_count", models.PositiveIntegerField(default=0)),
                ("slowest_query_ms", models.FloatField(default=0.0)),
                ("cache_hit", models.BooleanField(db_index=True, default=False)),
                ("cache_miss", models.BooleanField(db_index=True, default=False)),
                ("cache_key", models.CharField(blank=True, default="", max_length=255)),
                ("user_id", models.UUIDField(blank=True, db_index=True, null=True)),
                ("error", models.TextField(blank=True, default="")),
            ],
            options={
                "db_table": "api_request_metrics",
                "indexes": [
                    models.Index(fields=["path", "-created_at"], name="api_metric_path_time_idx"),
                    models.Index(fields=["status_code", "-created_at"], name="api_metric_status_time_idx"),
                    models.Index(fields=["duration_ms", "-created_at"], name="api_metric_duration_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="SlowQuery",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("request_id", models.CharField(db_index=True, max_length=64)),
                ("path", models.CharField(db_index=True, max_length=500)),
                ("duration_ms", models.FloatField(db_index=True)),
                ("sql", models.TextField()),
                (
                    "request_metric",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="slow_queries",
                        to="monitoring.apirequestmetric",
                    ),
                ),
            ],
            options={
                "db_table": "slow_queries",
                "indexes": [
                    models.Index(fields=["duration_ms", "-created_at"], name="slow_query_duration_idx"),
                    models.Index(fields=["path", "-created_at"], name="slow_query_path_time_idx"),
                ],
            },
        ),
    ]
