from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("calllogs", "0006_calllog_invalid_time"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="calllog",
            index=models.Index(
                fields=["branch", "call_type", "call_time"],
                name="calllog_branch_type_time_idx",
            ),
        ),
    ]
