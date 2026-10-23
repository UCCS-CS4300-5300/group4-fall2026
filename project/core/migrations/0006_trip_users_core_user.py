from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_merge_0002_trip_0004_alter_user_budget"),
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
