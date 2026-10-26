from django.db import models
import datetime
import json

class User(models.Model):
    """A class for storing a user and their trip preferences."""

    # The user's name. Note that this is supposed to be anonymous to other users, and is merely here as an internal identifier.
    name = models.CharField(max_length=50, default="Unknown")

    # A list of destinations the user wants to go to.
    destinations = models.JSONField(blank=True, default=list)

    # The user's individual budget for the trip.
    budget = models.DecimalField(null=True, blank=True, max_digits=100, decimal_places=2)

    # A list of activities the user wants to do. Stored as strings.
    activities = models.JSONField(blank=True, default=list)

    def add_destination(self, destination):
        """Adds destination to the user's list of destinations and saves it."""
        if destination not in self.destinations:
            self.destinations.append(destination)
            self.save(update_fields=["destinations"])

    def remove_destination(self, destination):
        """Removes destination from the user's list of destinations if present."""
        if destination in self.destinations:
            self.destinations.remove(destination)
            self.save(update_fields=["destinations"])

    def add_available_date_range(self, start, end):
        """Adds date to the user's list of available travel dates and saves it."""
        if start > end:
            raise ValueError('The start date must be before the end date.')
        date_range, _ = self.available_ranges.get_or_create(startDate=start, endDate=end)

    def remove_available_date_range(self, start, end):
        """Removes date from the user's list of available travel dates if present."""
        self.available_ranges.filter(startDate=start, endDate=end).delete()

    def add_activity(self, activity):
        """Adds activity to the user's list of preferred activities and saves it."""
        if activity not in self.activities:
            self.activities.append(activity)
            self.save(update_fields=["activities"])

    def remove_activity(self, activity):
        """Removes activity to the user's list of preferred activities if present."""
        if activity in self.activities:
            self.activities.remove(activity)
            self.save(update_fields=["activities"])


class DateRange(models.Model):
    """A class for storing ranges of available dates for trips."""

    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="available_ranges",null=True)
    startDate = models.DateField(default=datetime.date.today)
    endDate = models.DateField(default=datetime.date.today)

    def set_date_range(self, start, end):
        """Sets both the start and end dates for the date range. Input should use datetime.date objects."""
        if start > end:
            raise ValueError('The start date must be before the end date.')
        self.startDate = start
        self.endDate = end
        self.save()