import pytest
from django.urls import reverse
from .models import StarterItem, Trip, User, DateRange
from django.contrib.auth import get_user_model
from datetime import date

@pytest.mark.django_db
def test_model():
 item=StarterItem.objects.create(title="Example"); assert str(item)=="Example"

@pytest.mark.django_db
def test_trip_stores_metadata_ai_output_and_users():
 user_model=get_user_model()
 first_user=user_model.objects.create_user(username="traveler-one")
 second_user=user_model.objects.create_user(username="traveler-two")
 trip=Trip.objects.create(
  name="Coastal trip",
  metadata={"destination":"Oregon","days":5},
  ai_output="Visit the coast and local parks.",
 )
 trip.users.add(first_user,second_user)

 assert str(trip)=="Coastal trip"
 assert trip.metadata=={"destination":"Oregon","days":5}
 assert trip.ai_output=="Visit the coast and local parks."
 assert set(trip.users.all())=={first_user,second_user}
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

    dates = DateRange.objects.create()
    start = date(2026, 10, 22)
    end = date(2026, 10, 23)
    dates.set_date_range(start, end)

    user.add_available_date(dates)
    assert user.availableDates == [dates]

@pytest.mark.django_db
def test_user_remove_dates():
    user = User.objects.create(name = "Jeremiah")
    
    dates = DateRange.objects.create()
    start = date(2026, 10, 22)
    end = date(2026, 10, 23)
    dates.set_date_range(start, end)

    user.add_available_date(dates)
    user.remove_available_date(dates)
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

@pytest.mark.django_db
def test_set_date_range():
    dates = DateRange.objects.create()
    start = date(2026, 10, 22)
    end = date(2026, 10, 23)
    dates.set_date_range(start, end)
    assert (dates.startDate == start and dates.endDate == end)

@pytest.mark.django_db
def test_date_range_rejects_invalid_range():
    with pytest.raises(ValueError):
        dates = DateRange.objects.create()
        start = date(2026, 10, 23)
        end = date(2026, 10, 22)
        dates.set_date_range(start, end)