from django.db import models


class Trip(models.Model):
    name = models.CharField(max_length=120)

    users = models.ManyToManyField(
        "core.User",
        related_name="trips",
        blank=True,
    )

    metadata = models.JSONField(default=dict, blank=True)
    ai_output = models.TextField(blank=True)

    def add_user(self, user):
        self.users.add(user)

    def remove_user(self, user):
        self.users.remove(user)

    def update_user(self, user, **updates):
        self._require_user(user)
        fields = {
            field.name
            for field in user._meta.concrete_fields
            if not field.primary_key
        }
        invalid_fields = updates.keys() - fields
        if invalid_fields:
            raise ValueError(f"Invalid user field(s): {', '.join(sorted(invalid_fields))}")
        if updates:
            for field, value in updates.items():
                setattr(user, field, value)
            user.save(update_fields=list(updates))

    def get_user_data(self, user, field_name):
        self._require_user(user)
        if field_name not in {
            field.name
            for field in user._meta.concrete_fields
            if not field.primary_key
        }:
            raise ValueError(f"Invalid user field: {field_name}")
        return getattr(user, field_name)

    def _require_user(self, user):
        if user.pk is None or not self.users.filter(pk=user.pk).exists():
            raise ValueError("User is not associated with this trip.")

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