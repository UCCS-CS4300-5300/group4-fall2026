from django.urls import path
from . import views


urlpatterns = [
    path("", views.destination, name="home"),
    path("schedule/", views.schedule, name="schedule"),
    path("summary/", views.summary, name="summary"),
    path("ai-output/", views.ai_output, name="ai_output"),
]
