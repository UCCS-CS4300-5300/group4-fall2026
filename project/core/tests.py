import pytest
from django.urls import reverse
from .models import StarterItem, Trip, User, DateRange
from datetime import date

@pytest.mark.django_db
def test_model():
 item=StarterItem.objects.create(title="Example"); assert str(item)=="Example"

@pytest.mark.django_db
def test_trip_stores_metadata_ai_output_and_users():
 first_user=User.objects.create(name="traveler-one")
 second_user=User.objects.create(name="traveler-two")
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
    start = date(2026, 10, 22)
    end = date(2026, 10, 23)

    user.add_available_date_range(start, end)
    stored = user.available_ranges.get()

    assert stored.startDate == start
    assert stored.endDate == end

@pytest.mark.django_db
def test_user_remove_dates():
    user = User.objects.create(name = "Jeremiah")
    start = date(2026, 10, 22)
    end = date(2026, 10, 23)

    user.add_available_date_range(start, end)
    user.remove_available_date_range(start, end)
    
    assert user.available_ranges.count() == 0

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

# for trip.py
@pytest.mark.django_db
def test_trip_user_helpers_reject_invalid_fields():
    trip = Trip.objects.create(name="Winter break")
    user = User.objects.create(name="Quentin")
    trip.add_user(user)

    with pytest.raises(ValueError, match="Invalid user field"):
        trip.update_user(user, unknown_field="value")

    with pytest.raises(ValueError, match="Invalid user field"):
        trip.get_user_data(user, "unknown_field")


@pytest.mark.django_db
def test_trip_defaults_and_ai_output_persist():
    trip = Trip.objects.create(name="Winter break")

    assert trip.metadata == {}
    assert trip.ai_output == ""

    trip.metadata = {"destination": "Oregon"}
    trip.ai_output = "Visit the coast."
    trip.save()
    trip.refresh_from_db()

    assert trip.metadata == {"destination": "Oregon"}
    assert trip.ai_output == "Visit the coast."

@pytest.mark.django_db
def test_trip_access_user_attribute():
   trip = Trip.objects.create(name="Winter break")
   user = User.objects.create(name="Quentin")
   trip.add_user(user)
   returnAtt = trip.get_user_data(user, "name")
   assert returnAtt == "Quentin"