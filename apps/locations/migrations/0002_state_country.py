from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("locations", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="state",
            name="country",
            field=models.CharField(default="India", max_length=120),
        ),
    ]
