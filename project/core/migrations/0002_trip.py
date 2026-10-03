from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Trip",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=120)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("ai_output", models.TextField(blank=True)),
                (
                    "users",
                    models.ManyToManyField(
                        blank=True,
                        related_name="trips",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]