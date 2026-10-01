import pytest
from django.urls import reverse
from .models import StarterItem
from .models import User
from datetime import date

@pytest.mark.django_db
def test_model():
 item=StarterItem.objects.create(title="Example"); assert str(item)=="Example"
@pytest.mark.django_db
def test_home(client):
 r=client.get(reverse("core:home")); assert r.status_code==200; assert b"Your project starts here." in r.content
@pytest.mark.django_db
def test_only_active(client):
 StarterItem.objects.create(title="Visible",is_active=True); StarterItem.objects.create(title="Hidden",is_active=False)
 r=client.get(reverse("core:home")); assert b"Visible" in r.content; assert b"Hidden" not in r.content


@pytest.mark.django_db
def test_user_name_set():
    user = User.objects.create(name = "Jeremiah")
    assert user.name == "Jeremiah"

@pytest.mark.django_db
def test_user_add_destinations():
    user = User.objects.create(name = "Jeremiah")
    user.add_destination("Arizona")
    user.add_destination("Paris")
    assert user.destinations == ["Arizona", "Paris"]

@pytest.mark.django_db
def test_user_remove_destinations():
    user = User.objects.create(name = "Jeremiah")
    user.add_destination("Arizona")
    user.remove_destination("Arizona")
    assert user.destinations == []

@pytest.mark.django_db
def test_user_add_dates():
    user = User.objects.create(name = "Jeremiah")
    user.add_available_date(date(2026, 9, 30).isoformat())
    user.add_available_date(date(2026, 10, 1).isoformat())
    assert user.availableDates == [date(2026, 9, 30).isoformat(), date(2026, 10, 1).isoformat()]

@pytest.mark.django_db
def test_user_remove_dates():
    user = User.objects.create(name = "Jeremiah")
    user.add_available_date(date(2026, 9, 30).isoformat())
    user.remove_available_date(date(2026, 9, 30).isoformat())
    assert user.availableDates == []

@pytest.mark.django_db
def test_user_add_activities():
    user = User.objects.create(name = "Jeremiah")
    user.add_activity("Surfing")
    user.add_activity("Hiking")
    assert user.activities == ["Surfing", "Hiking"]

@pytest.mark.django_db
def test_user_remove_activities():
    user = User.objects.create(name = "Jeremiah")
    user.add_activity("Surfing")
    user.remove_activity("Surfing")
    assert user.activities == []