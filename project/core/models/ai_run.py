"""AIRun: the state of the background AI run for one trip."""
from django.db import models


class AIRun(models.Model):
    """
    The latest AI run for one trip: whether it is running, which answers it
    used, and any AI output that has no other home yet.
    """

    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    STATUS_CHOICES = [
        (IDLE, "Not started"),
        (RUNNING, "Running"),
        (DONE, "Done"),
        (FAILED, "Failed"),
    ]

    trip = models.OneToOneField("core.Trip", on_delete=models.CASCADE, related_name="ai_run")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=IDLE)
    # Fingerprint of the members' answers this run used; a change means the results are out of date.
    inputs = models.CharField(max_length=64, blank=True)
    # Short, user-facing reason when status is FAILED.
    error = models.CharField(max_length=255, blank=True)
    # AI output not stored elsewhere yet, e.g. {"activities": {"short": ..., "long": ...}}.
    results = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.trip} AI run: {self.status}"