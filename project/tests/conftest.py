"""
Shared fixtures for the model tests in tests/test_models.py.

These began as the Sprint 1 starter tests, which skipped until each
teammate's code existed. That code has landed, so the fixtures import it
directly: a missing model or field is now a real failure, not a skip.
"""
import datetime as dt
from decimal import Decimal

import pytest

from core.models import Trip, User

TRIP_USERS_FIELD = "users"   # Trip's many-to-many field to User
TRIP_AI_FIELD = "ai_output"  # Trip's field holding the AI's reply

DATE_1 = dt.date.today() + dt.timedelta(days=60)
DATE_2 = dt.date.today() + dt.timedelta(days=61)


@pytest.fixture
def user_model():
    return User


@pytest.fixture
def trip_model():
    return Trip


@pytest.fixture
def trip_users_target(trip_model):
    """The model that Trip's users field actually points at."""
    return trip_model._meta.get_field(TRIP_USERS_FIELD).related_model


@pytest.fixture
def ai_field():
    return TRIP_AI_FIELD


@pytest.fixture
def users_of():
    """users_of(trip) returns the trip's related manager for its users."""
    return lambda trip: getattr(trip, TRIP_USERS_FIELD)


@pytest.fixture
def trip_with_users(db, trip_model, user_model, users_of):
    """A saved trip with three users whose preferences overlap on Austin."""
    trip = trip_model.objects.create(name="Winter break")
    rows = [
        # name,       destinations,          budget, activities
        ("Quentin",   ["Denver", "Austin"],  "450",  ["skiing"]),
        ("Rosalind",  ["Austin", "Chicago"], "600",  ["live music"]),
        ("Thaddeus",  ["Austin", "Miami"],   "900",  ["beach"]),
    ]
    for name, destinations, budget, activities in rows:
        user = user_model.objects.create(
            name=name,
            destinations=destinations,
            budget=Decimal(budget),
            activities=activities,
        )
        user.add_available_date_range(DATE_1, DATE_2)
        users_of(trip).add(user)
    return trip

@pytest.fixture
def log_in(client):
    """
    log_in(trip, user) signs the test client in as user on trip, the way the
    create and join pages do. Pages that need a participant redirect to the
    start page without it.
    """
    def _log_in(trip, user):
        session = client.session
        session["active_trip_id"] = trip.pk
        session["active_user_id"] = user.pk
        session.save()

    return _log_in
