from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("matching", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="matchresult",
            name="hired",
            field=models.BooleanField(blank=True, db_index=True, null=True),
        ),
    ]
