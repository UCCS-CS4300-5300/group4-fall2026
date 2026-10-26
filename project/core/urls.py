from django.urls import path,include
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("destination/", views.destination, name="destination"),
    path("schedule/", views.schedule, name="schedule"),
    path("budget/", views.budget, name="budget"),
    path("activities/", views.activities, name="activities"),
    path("summary/", views.summary, name="summary"),
    path("ai-output/", views.ai_output, name="ai_output"),
]
