from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("datasets", "0043_dataset_data_input_map_button_flags"),
    ]

    operations = [
        migrations.AddField(
            model_name="dataset",
            name="data_input_add_point_label",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Label for the Add Point button on the data-input map. Leave blank for default.",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="dataset",
            name="data_input_my_location_label",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Label for the My Location button on the data-input map. Leave blank for default.",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="dataset",
            name="anonymous_welcome_title",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Title of the anonymous welcome modal. Leave blank for default.",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="dataset",
            name="anonymous_name_field_label",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Label for the optional name field in the anonymous welcome modal. Leave blank for default.",
                max_length=255,
            ),
        ),
    ]
