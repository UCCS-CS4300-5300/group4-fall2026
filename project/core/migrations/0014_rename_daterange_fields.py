from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0013_aiactivities"),
    ]

    operations = [
        migrations.RenameField(model_name="daterange", old_name="startDate", new_name="start_date"),
        migrations.RenameField(model_name="daterange", old_name="endDate", new_name="end_date"),
    ]
