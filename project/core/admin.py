from django.contrib import admin
from .models import StarterItem, Trip, User
from .models.trip import AISuggestion
from .models.user import DateRange


class DateRangeInline(admin.TabularInline):
    """Lets a user's available date ranges be edited on the user's own admin page."""
    model = DateRange
    extra = 1


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    inlines = [DateRangeInline]


admin.site.register(StarterItem)
# Registered so test data for the summary and AI output pages can be added at /admin/.
admin.site.register(Trip)
admin.site.register(AISuggestion)
