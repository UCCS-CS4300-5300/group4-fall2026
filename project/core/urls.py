from django.urls import path
from . import views


urlpatterns = [
    path("", views.destination, name="home"),
    path("schedule/", views.schedule, name="schedule"),
]
