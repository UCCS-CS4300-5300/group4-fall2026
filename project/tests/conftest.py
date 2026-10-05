"""
Shared fixtures for the Sprint 1 starter tests.

The form, Trip model, and AI caller are still being written, so every
import goes through require(). If a teammate's module or class doesn't
exist yet, the test is SKIPPED instead of failing. Once their code lands,
the skips become real passes or failures on their own.

If a teammate picks different names, change the constants below. The
tests themselves shouldn't need editing.
"""
import datetime as dt
import importlib
from decimal import Decimal

import pytest

APP = "core"

FORM = (f"{APP}.forms", "SubmissionForm")    # Andrew
USER = (f"{APP}.models", "User")             # Roy (exists on user_object_branch)
TRIP = (f"{APP}.models", "Trip")             # Evan
TRIP_USERS_FIELD = "users"                   # Trip's many-to-many field to User
TRIP_AI_FIELD = "ai_output"                  # Trip's field holding the AI's reply
AI_MODULE = f"{APP}.ai"                      # Joe
AI_FUNCTIONS = ("build_prompt", "call_model", "suggest_destination")

DATE_1 = (dt.date.today() + dt.timedelta(days=60)).isoformat()
DATE_2 = (dt.date.today() + dt.timedelta(days=61)).isoformat()


def require(module_path, name=None):
    """Import module_path (and optionally one name from it), skipping if absent."""
    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        # Skip only when OUR module is missing. A missing package imported
        # inside a teammate's code is a real bug and should fail loudly.
        if exc.name and (module_path == exc.name or module_path.startswith(exc.name + ".")):
            pytest.skip(f"{module_path} doesn't exist yet")
        raise
    if name is None:
        return module
    if not hasattr(module, name):
        pytest.skip(f"{module_path}.{name} doesn't exist yet")
    return getattr(module, name)


@pytest.fixture
def submission_form_cls():
    return require(*FORM)


@pytest.fixture
def user_model():
    return require(*USER)


@pytest.fixture
def trip_model():
    return require(*TRIP)


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
def ai():
    module = require(AI_MODULE)
    missing = [f for f in AI_FUNCTIONS if not hasattr(module, f)]
    if missing:
        pytest.skip(f"{AI_MODULE} is missing: {', '.join(missing)}")
    return module


@pytest.fixture
def valid_submission():
    """
    Raw form data for one person, as the browser would POST it.

    ASSUMPTION: list fields are typed as comma-separated text. If Andrew's
    form takes them another way, change this fixture and expected_user_data.
    """
    return {
        "destinations": "Denver, Austin, Chicago",
        "availableDates": f"{DATE_1}, {DATE_2}",
        "budget": "800.00",
        "activities": "hiking, live music",
    }


@pytest.fixture
def expected_user_data():
    """What the saved User should contain after valid_submission goes through the form."""
    return {
        "destinations": ["Denver", "Austin", "Chicago"],
        "availableDates": [DATE_1, DATE_2],
        "budget": Decimal("800.00"),
        "activities": ["hiking", "live music"],
    }


@pytest.fixture
def trip_with_users(db, trip_model, user_model, users_of, trip_users_target):
    """A saved trip with three users whose preferences overlap on Austin."""
    if trip_users_target is not user_model:
        pytest.skip(
            f"Trip.{TRIP_USERS_FIELD} links to {trip_users_target._meta.label}, "
            f"not {user_model._meta.label}; see test_trip_links_to_core_users"
        )
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
            availableDates=[DATE_1, DATE_2],
            budget=Decimal(budget),
            activities=activities,
        )
        users_of(trip).add(user)
    return trip
