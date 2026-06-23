from django.db import migrations


def seed_channels(apps, schema_editor):
    DoubleTickChannel = apps.get_model("doubletick", "DoubleTickChannel")
    for number in ["918976822800", "918976822802"]:
        DoubleTickChannel.objects.get_or_create(
            waba_number=number,
            defaults={
                "name": f"DoubleTick {number}",
                "is_active": True,
                "description": "Seeded WABA channel for DoubleTick WhatsApp CRM integration.",
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("doubletick", "0006_distribution_audit_visibility_constraints"),
    ]

    operations = [
        migrations.RunPython(seed_channels, migrations.RunPython.noop),
    ]
