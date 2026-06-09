from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("datasets", "0042_dataset_anonymous_welcome_message"),
    ]

    operations = [
        migrations.AddField(
            model_name="dataset",
            name="data_input_show_focus_all",
            field=models.BooleanField(
                default=True,
                help_text="When enabled, contributors see the Focus All button on the data-input map.",
            ),
        ),
        migrations.AddField(
            model_name="dataset",
            name="data_input_show_goto_location",
            field=models.BooleanField(
                default=True,
                help_text="When enabled, contributors see the Goto location button on the data-input map.",
            ),
        ),
    ]
