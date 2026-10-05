from django.conf import settings
from django.db import models


class Trip(models.Model):
    name = models.CharField(max_length=120)
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="trips",
        blank=True,
    )
    metadata = models.JSONField(default=dict, blank=True)
    ai_output = models.TextField(blank=True)

    def __str__(self):
        return self.name