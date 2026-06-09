from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("datasets", "0041_merge_20260527_1650"),
    ]

    operations = [
        migrations.AddField(
            model_name="dataset",
            name="anonymous_welcome_message",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Intro text shown in the anonymous welcome modal. Leave blank to use the default.",
            ),
        ),
    ]
