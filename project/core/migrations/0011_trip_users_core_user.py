from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0010_remove_user_availabledates_daterange_user_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="trip",
            name="users",
            field=models.ManyToManyField(
                blank=True,
                related_name="trips",
                to="core.user",
            ),
        ),
    ]
