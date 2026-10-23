from django.contrib import admin
from .models import StarterItem, Trip, User
from .models.trip import AISuggestion

admin.site.register(StarterItem)
# Registered so test data for the summary and AI output pages can be added at /admin/.
admin.site.register(User)
admin.site.register(Trip)
admin.site.register(AISuggestion)
