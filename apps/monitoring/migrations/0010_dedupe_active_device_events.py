from django.db import migrations, models
from django.db.models import Count, Q


def merge_active_device_event_duplicates(apps, schema_editor):
    DeviceEvent = apps.get_model("monitoring", "DeviceEvent")
    db_alias = schema_editor.connection.alias

    duplicate_groups = (
        DeviceEvent.objects.using(db_alias)
        .filter(resolved=False)
        .values("device_id", "event_type")
        .annotate(row_count=Count("id"))
        .filter(row_count__gt=1)
    )

    for group in duplicate_groups.iterator():
        events = list(
            DeviceEvent.objects.using(db_alias)
            .filter(
                device_id=group["device_id"],
                event_type=group["event_type"],
                resolved=False,
            )
            .order_by("created_at", "id")
        )
        if len(events) <= 1:
            continue

        canonical = events[0]
        duplicates = events[1:]
        descriptions = [event.description for event in events if event.description]
        latest_updated_at = max((event.updated_at for event in events if event.updated_at), default=canonical.updated_at)

        update_values = {}
        if descriptions and canonical.description != descriptions[-1]:
            update_values["description"] = descriptions[-1]
        if latest_updated_at and canonical.updated_at != latest_updated_at:
            update_values["updated_at"] = latest_updated_at

        if update_values:
            DeviceEvent.objects.using(db_alias).filter(pk=canonical.pk).update(**update_values)

        DeviceEvent.objects.using(db_alias).filter(pk__in=[event.pk for event in duplicates]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("monitoring", "0009_devicehealth_network_status"),
    ]

    operations = [
        migrations.RunPython(
            merge_active_device_event_duplicates,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="deviceevent",
            constraint=models.UniqueConstraint(
                fields=("device", "event_type"),
                condition=Q(resolved=False),
                name="uniq_active_device_event_type",
            ),
        ),
    ]
