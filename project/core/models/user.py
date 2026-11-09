
import datetime

from django.db import models


class User(models.Model):
    """
    Individual participant in a trip.

    This is a custom participant model, not Django's
    authentication User model.
    """

    name = models.CharField(
        max_length=50,
        default="Unknown"
    )

    destinations = models.JSONField(
        blank=True,
        default=list
    )

    budget = models.DecimalField(
        null=True,
        blank=True,
        max_digits=12,
        decimal_places=2
    )

    currency = models.CharField(
        max_length=3,
        default="USD"
    )

    activities = models.JSONField(
        blank=True,
        default=list
    )

    additional_notes = models.TextField(
        blank=True,
        default=""
    )

    schedule_preferences = models.JSONField(
        blank=True,
        default=dict
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def add_destination(self, destination):
        if destination not in self.destinations:
            self.destinations.append(destination)
            self.save(update_fields=["destinations"])

    def remove_destination(self, destination):
        if destination in self.destinations:
            self.destinations.remove(destination)
            self.save(update_fields=["destinations"])

    def add_available_date_range(self, start, end):
        if start > end:
            raise ValueError(
                "The start date must be before the end date."
            )

        return self.available_ranges.get_or_create(
            startDate=start,
            endDate=end
        )

    def remove_available_date_range(self, start, end):
        self.available_ranges.filter(
            startDate=start,
            endDate=end
        ).delete()

    def add_activity(self, activity):
        if activity not in self.activities:
            self.activities.append(activity)
            self.save(update_fields=["activities"])

    def remove_activity(self, activity):
        if activity in self.activities:
            self.activities.remove(activity)
            self.save(update_fields=["activities"])

    def __str__(self):
        return self.name


class DateRange(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="available_ranges",
        null=True,
        blank=True
    )

    startDate = models.DateField(
        default=datetime.date.today
    )

    endDate = models.DateField(
        default=datetime.date.today
    )

    def set_date_range(self, start, end):
        if start > end:
            raise ValueError(
                "The start date must be before the end date."
            )

        self.startDate = start
        self.endDate = end
        self.save()

    def __str__(self):
        return f"{self.startDate} - {self.endDate}"
