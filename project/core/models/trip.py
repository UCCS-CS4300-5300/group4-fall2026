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

    def __str__(self):
        return self.name


class AISuggestion(models.Model):
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name="suggestions"
    )

    location = models.CharField(max_length=255)

    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.location