"""User object (Roy) and Trip object (Evan)."""
from decimal import Decimal

import pytest


def _looks_like_ai_output(field_name):
    words = field_name.lower().split("_")
    return "ai" in words or any(
        w.startswith(("suggest", "recommend", "generated")) for w in words
    )


# ---- User (Roy) -------------------------------------------------------------

def test_user_stores_no_ai_output(user_model):
    """User holds only what the person typed in. AI results belong on Trip."""
    offenders = [
        f.name for f in user_model._meta.get_fields() if _looks_like_ai_output(f.name)
    ]
    assert offenders == []


@pytest.mark.django_db
def test_user_changes_are_saved_to_database(user_model):
    """The add_* helpers should persist, not just change the object in memory."""
    user = user_model.objects.create(name="Quentin")
    user.add_destination("Paris")
    user.add_available_date("2026-12-18")
    user.add_activity("Hiking")

    fresh = user_model.objects.get(pk=user.pk)
    assert fresh.destinations == ["Paris"]
    assert fresh.availableDates == ["2026-12-18"]
    assert fresh.activities == ["Hiking"]


@pytest.mark.django_db
def test_users_do_not_share_lists(user_model):
    """Adding to one user's list must never show up on another user."""
    first = user_model.objects.create(name="Quentin")
    second = user_model.objects.create(name="Rosalind")
    first.add_destination("Paris")
    assert second.destinations == []


@pytest.mark.django_db
def test_budget_keeps_exact_cents(user_model):
    user = user_model.objects.create(name="Quentin", budget=Decimal("799.99"))
    user.refresh_from_db()
    assert user.budget == Decimal("799.99")


# ---- Trip (Evan) ------------------------------------------------------------

def test_trip_links_to_core_users(trip_users_target, user_model):
    """Trip must hold our User objects so the AI can read everyone's preferences."""
    assert trip_users_target is user_model, (
        f"Trip.users links to {trip_users_target._meta.label} (Django's login accounts), "
        f"but it should link to {user_model._meta.label}, which holds destinations and budgets"
    )


def test_trip_has_a_field_for_ai_output(trip_model, ai_field):
    names = {f.name for f in trip_model._meta.get_fields()}
    assert ai_field in names


@pytest.mark.django_db
def test_ai_output_starts_empty_and_persists(trip_model, ai_field):
    trip = trip_model.objects.create(name="Winter break")
    assert not getattr(trip, ai_field)
    setattr(trip, ai_field, "Austin")
    trip.save()
    trip.refresh_from_db()
    assert getattr(trip, ai_field) == "Austin"


def test_trip_contains_its_users(trip_with_users, users_of):
    assert users_of(trip_with_users).count() == 3


@pytest.mark.django_db
def test_users_do_not_leak_between_trips(trip_with_users, trip_model, users_of):
    other = trip_model.objects.create(name="Spring break")
    assert users_of(other).count() == 0


@pytest.mark.django_db
def test_trip_user_helpers_manage_and_access_user_data(trip_model, user_model):
    trip = trip_model.objects.create(name="Winter break")
    user = user_model.objects.create(name="Quentin", budget=Decimal("450.00"))

    trip.add_user(user)
    assert trip.get_user_data(user, "budget") == Decimal("450.00")

    trip.update_user(user, budget=Decimal("600.00"), activities=["hiking"])
    user.refresh_from_db()
    assert user.budget == Decimal("600.00")
    assert user.activities == ["hiking"]

    trip.remove_user(user)
    assert not trip.users.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_trip_cannot_update_or_read_unassociated_user(trip_model, user_model):
    trip = trip_model.objects.create(name="Winter break")
    user = user_model.objects.create(name="Quentin")

    with pytest.raises(ValueError, match="not associated"):
        trip.update_user(user, name="Rosalind")
    with pytest.raises(ValueError, match="not associated"):
        trip.get_user_data(user, "name")
