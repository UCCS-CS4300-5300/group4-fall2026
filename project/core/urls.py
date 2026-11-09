
from django.urls import path
from . import views

app_name = "core"

urlpatterns = [

    # Create a trip.
    path("", views.home, name="home"),

    # Join an existing trip.
    path("join/", views.join_trip, name="join_trip"),

    # Individual participant preferences.
    path("destination/", views.destination, name="destination"),
    path("schedule/", views.schedule, name="schedule"),
    path("budget/", views.budget, name="budget"),
    path("activities/", views.activities, name="activities"),

    # Combined group results.
    path("summary/", views.summary, name="summary"),

    # AI recommendations.
    path("ai-output/", views.ai_output, name="ai_output"),
    path("ai/run/", views.ai_run, name="ai_run"),
    path("ai/status/", views.ai_status, name="ai_status"),
]
