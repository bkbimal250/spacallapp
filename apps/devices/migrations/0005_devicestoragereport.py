from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("devices", "0004_lastsynchistory"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeviceStorageReport",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("total_app_storage_mb", models.FloatField(default=0)),
                ("db_size_mb", models.FloatField(default=0)),
                ("cache_size_mb", models.FloatField(default=0)),
                ("audio_size_mb", models.FloatField(default=0)),
                ("log_size_mb", models.FloatField(default=0)),
                ("temp_size_mb", models.FloatField(default=0)),
                ("other_size_mb", models.FloatField(default=0)),
                ("unsynced_call_count", models.IntegerField(default=0)),
                ("pending_sync_count", models.IntegerField(default=0)),
                ("failed_sync_count", models.IntegerField(default=0)),
                ("cleanup_deleted_records_count", models.IntegerField(default=0)),
                ("cleanup_deleted_files_count", models.IntegerField(default=0)),
                ("cleanup_freed_mb", models.FloatField(default=0)),
                ("last_cleanup_at", models.DateTimeField(blank=True, null=True)),
                ("reported_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("storage_status", models.CharField(db_index=True, default="NORMAL", max_length=16)),
                ("raw_payload", models.JSONField(blank=True, default=dict)),
                ("device", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="storage_reports", to="devices.device")),
            ],
            options={
                "db_table": "device_storage_reports",
            },
        ),
        migrations.AddIndex(
            model_name="devicestoragereport",
            index=models.Index(fields=["device", "-reported_at"], name="device_stor_device__fa624d_idx"),
        ),
        migrations.AddIndex(
            model_name="devicestoragereport",
            index=models.Index(fields=["storage_status", "-reported_at"], name="device_stor_storage_43b142_idx"),
        ),
    ]
