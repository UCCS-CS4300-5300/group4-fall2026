"""Creating and joining trips: the session keys every page relies on, and the invite link."""
import pytest
from django.test import Client
from django.urls import reverse

from core.models import Trip

pytestmark = pytest.mark.django_db


def create(client, trip_name="Vegas", person="Ann"):
    return client.post(reverse("core:home"), {"tripName": trip_name, "personName": person})


def join(client, code, person):
    return client.post(reverse("core:join_trip"), {"invite_code": code, "person_name": person})


def test_creating_a_trip_signs_the_creator_in(client):
    r = create(client)
    trip = Trip.objects.get()
    creator = trip.users.get()
    assert r.status_code == 302 and r.url == reverse("core:destination")
    assert creator.name == "Ann"
    assert client.session["active_trip_id"] == trip.pk
    assert client.session["active_user_id"] == creator.pk


def test_each_new_trip_gets_its_own_invite_code(client):
    create(client, "Vegas")
    create(Client(), "Vegas")
    codes = list(Trip.objects.values_list("invite_code", flat=True))
    assert len(codes) == 2 and len(set(codes)) == 2
    assert all(len(code) == 8 for code in codes)


def test_joining_with_the_code_adds_a_member(client):
    create(client)
    trip = Trip.objects.get()
    friend = Client()
    r = join(friend, trip.invite_code.lower() + "  ", "Bo")  # case and spaces don't matter
    assert r.status_code == 302 and r.url == reverse("core:destination")
    assert sorted(trip.users.values_list("name", flat=True)) == ["Ann", "Bo"]
    assert friend.session["active_trip_id"] == trip.pk


def test_rejoining_with_the_same_name_continues_as_that_member(client):
    create(client)
    trip = Trip.objects.get()
    ann = trip.users.get()
    new_browser = Client()
    join(new_browser, trip.invite_code, "  ann ")
    assert trip.users.count() == 1
    assert new_browser.session["active_user_id"] == ann.pk


def test_a_wrong_code_is_rejected_and_keeps_what_was_typed(client):
    create(client)
    r = join(Client(), "NOPE1234", "Bo")
    html = r.content.decode()
    assert r.status_code == 400
    assert "Invalid invitation code." in html
    assert 'value="NOPE1234"' in html and 'value="Bo"' in html
    assert Trip.objects.get().users.count() == 1


def test_the_invite_link_fills_in_the_code(client):
    r = client.get(reverse("core:join_trip") + "?code=abc12345")
    assert r.status_code == 200
    assert 'value="ABC12345"' in r.content.decode()


def test_summary_offers_the_invite_link(client):
    create(client)
    trip = Trip.objects.get()
    html = client.get(reverse("core:summary")).content.decode()
    assert f'data-link="{reverse("core:join_trip")}?code={trip.invite_code}"' in html
