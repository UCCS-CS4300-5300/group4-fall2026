import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import StarterItem, Trip
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
