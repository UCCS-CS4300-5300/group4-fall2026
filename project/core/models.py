from django.db import models
class StarterItem(models.Model):
 title=models.CharField(max_length=120)
 description=models.TextField(blank=True)
 is_active=models.BooleanField(default=True)
 def __str__(self): return self.title


class User(models.Model):
    """A class for storing a user and their trip preferences."""

    # The user's name. Note that this is supposed to be anonymous to other users, and is merely here as an internal identifier.
    name = models.CharField(max_length=50, default="Unknown")

    # A list of destinations the user wants to go to.
    destinations = models.JSONField(blank=True, default=list)

    # A list of dates the user is available to go on vacation for.
    availableDates = models.JSONField(blank=True, default=list)

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

    def add_available_date(self, date):
        """Adds date to the user's list of available travel dates and saves it."""
        if date not in self.availableDates:
            self.availableDates.append(date)
            self.save(update_fields=["availableDates"])

    def remove_available_date(self, date):
        """Removes date from the user's list of available travel dates if present."""
        if date in self.availableDates:
            self.availableDates.remove(date)
            self.save(update_fields=["availableDates"])

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