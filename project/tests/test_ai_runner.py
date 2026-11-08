"""
Background AI runs: when the AI is called, what gets saved, and the
run/status endpoints the pages poll. Ollama is always faked.
"""
import datetime as dt
from decimal import Decimal
from types import SimpleNamespace

import ollama
import pytest
from django.urls import reverse
from django.utils import timezone

from core import ai_runner
from core.models import AIRun, Trip, User
from core.models.trip import AISuggestion

DEST_REPLY = "**Austin, Texas, USA**\nAustin overlaps most picks and fits every budget."
ACT_REPLY = (
    "1. **Hiking, Barton Creek Greenbelt**\n2. **Live music, Sixth Street**\n"
    "3. **Swimming, Barton Springs Pool**\n\nA mix of outdoors and nightlife."
)


@pytest.fixture
def fake_ai(monkeypatch):
    """Replace ollama.chat. Records each call; set fake_ai.fail to raise instead of replying."""
    fake = SimpleNamespace(calls=[], fail=None, dest_reply=DEST_REPLY)

    def chat(model, messages):
        is_activities = "suggesting a set of activities" in messages[0]["content"]
        fake.calls.append("activities" if is_activities else "destination")
        if fake.fail:
            raise fake.fail
        return {"message": {"content": ACT_REPLY if is_activities else fake.dest_reply}}

    monkeypatch.setattr(ollama, "chat", chat)
    return fake


@pytest.fixture
def run_now(monkeypatch):
    """Run the AI in the test itself instead of a background thread."""
    monkeypatch.setattr(ai_runner, "launch", ai_runner.run_ai)


@pytest.fixture
def trip(db):
    trip = Trip.objects.create(name="Winter break")
    for name, dests, acts in [
        ("Quentin", ["Denver", "Austin"], ["hiking"]),
        ("Rosalind", ["Austin"], ["live music"]),
    ]:
        user = User.objects.create(name=name, destinations=dests, activities=acts, budget=Decimal("600"))
        trip.add_user(user)
    return trip


def member(trip):
    return trip.users.order_by("pk").first()


# ---- When the AI is called ---------------------------------------------------

def test_a_run_asks_for_destination_then_activities_and_saves_both(trip, fake_ai, run_now):
    result = ai_runner.start(trip)

    assert result["status"] == "running"
    assert fake_ai.calls == ["destination", "activities"]
    suggestion = AISuggestion.objects.get(trip=trip)
    assert suggestion.location == "Austin, Texas, USA"
    assert suggestion.description == "Austin overlaps most picks and fits every budget."
    run = AIRun.objects.get(trip=trip)
    assert run.status == AIRun.DONE and run.finished_at is not None
    assert run.results["activities"]["short"] == (
        "Hiking, Barton Creek Greenbelt, Live music, Sixth Street, Swimming, Barton Springs Pool"
    )
    assert run.results["activities"]["long"] == "A mix of outdoors and nightlife."
    assert ai_runner.state(trip) == {"status": "done", "up_to_date": True, "error": ""}


def test_unchanged_answers_do_not_call_the_ai_again(trip, fake_ai, run_now):
    ai_runner.start(trip)
    ai_runner.start(trip)
    ai_runner.start(trip)
    assert fake_ai.calls == ["destination", "activities"]
    assert AISuggestion.objects.filter(trip=trip).count() == 1


@pytest.mark.parametrize("change", [
    lambda u: u.add_destination("Chicago"),
    lambda u: u.add_activity("kayaking"),
    lambda u: User.objects.filter(pk=u.pk).update(budget=Decimal("900")),
    lambda u: u.add_available_date_range(dt.date(2026, 12, 18), dt.date(2026, 12, 20)),
])
def test_changed_answers_make_results_out_of_date_and_start_a_new_run(trip, fake_ai, run_now, change):
    ai_runner.start(trip)
    change(member(trip))
    assert ai_runner.state(trip)["up_to_date"] is False

    ai_runner.start(trip)
    assert fake_ai.calls == ["destination", "activities"] * 2


def test_a_new_member_makes_results_out_of_date(trip, fake_ai, run_now):
    ai_runner.start(trip)
    trip.add_user(User.objects.create(name="Thaddeus", destinations=["Miami"]))
    assert ai_runner.state(trip)["up_to_date"] is False


def test_no_second_run_starts_while_one_is_running(trip, monkeypatch):
    launched = []
    monkeypatch.setattr(ai_runner, "launch", launched.append)
    ai_runner.start(trip)
    ai_runner.start(trip)
    assert len(launched) == 1
    assert ai_runner.state(trip)["status"] == "running"


def test_a_run_stuck_too_long_is_reported_failed_and_restarted(trip, monkeypatch):
    launched = []
    monkeypatch.setattr(ai_runner, "launch", launched.append)
    ai_runner.start(trip)
    AIRun.objects.filter(trip=trip).update(started_at=timezone.now() - dt.timedelta(minutes=11))

    assert ai_runner.state(trip) == {
        "status": "failed", "up_to_date": True, "error": "The last run did not finish.",
    }
    ai_runner.start(trip)
    assert len(launched) == 2


def test_trip_with_no_members_never_calls_the_ai(db, fake_ai, run_now):
    empty = Trip.objects.create(name="Empty")
    assert ai_runner.start(empty)["status"] == "idle"
    assert fake_ai.calls == []
    assert not AIRun.objects.filter(trip=empty).exists()


def test_launch_uses_a_background_thread(monkeypatch):
    started = []

    class FakeThread:
        def __init__(self, target, daemon, name):
            started.append((daemon, name))

        def start(self):
            started.append("started")

    monkeypatch.setattr(ai_runner.threading, "Thread", FakeThread)
    ai_runner.launch(7)
    assert started == [(True, "trip-ai-run-7"), "started"]


@pytest.mark.parametrize("raw, expected", [
    ("**Austin, Texas, USA**\nGood fit.", "Good fit."),
    ("1. **A, X**\n2. **B, Y**\n\nWhy these.", "Why these."),
    ("**Austin**", "Austin"),            # nothing after the answer: keep the answer
    ("No bold at all.", "No bold at all."),
])
def test_explanation_drops_the_bold_answer(raw, expected):
    assert ai_runner._explanation(raw) == expected  # pylint: disable=protected-access


# ---- When the AI fails -------------------------------------------------------

def test_ai_service_down_fails_the_run_with_a_clear_message(trip, fake_ai, run_now):
    fake_ai.fail = ConnectionError("Failed to connect to Ollama")
    ai_runner.start(trip)
    assert ai_runner.state(trip) == {
        "status": "failed", "up_to_date": True, "error": "The AI service isn't available right now.",
    }
    assert not AISuggestion.objects.filter(trip=trip).exists()


def test_a_failed_run_is_only_repeated_on_retry(trip, fake_ai, run_now):
    fake_ai.fail = ConnectionError("down")
    ai_runner.start(trip)
    ai_runner.start(trip)
    assert fake_ai.calls == ["destination"]

    fake_ai.fail = None
    ai_runner.start(trip, retry=True)
    assert fake_ai.calls == ["destination", "destination", "activities"]
    assert ai_runner.state(trip)["status"] == "done"


def test_reply_without_a_bold_destination_fails_the_run(trip, fake_ai, run_now):
    fake_ai.dest_reply = "I'd suggest Austin."
    ai_runner.start(trip)
    assert ai_runner.state(trip)["error"] == "The AI's reply wasn't in the expected format. Try again."


def test_no_destinations_fails_without_calling_the_ai(db, fake_ai, run_now):
    trip = Trip.objects.create(name="Undecided")
    trip.add_user(User.objects.create(name="Quentin", activities=["hiking"]))
    ai_runner.start(trip)
    assert fake_ai.calls == []
    assert ai_runner.state(trip)["error"] == "Add at least one destination before asking the AI."


def test_no_activities_still_saves_the_destination(db, fake_ai, run_now):
    trip = Trip.objects.create(name="Just going")
    trip.add_user(User.objects.create(name="Quentin", destinations=["Austin"]))
    ai_runner.start(trip)
    assert fake_ai.calls == ["destination"]
    run = AIRun.objects.get(trip=trip)
    assert run.status == AIRun.DONE and "activities" not in run.results
    assert AISuggestion.objects.filter(trip=trip).exists()


# ---- The endpoints the pages use ----------------------------------------------

def activate(client, trip):
    session = client.session
    session["active_trip_id"] = trip.pk
    session.save()


def test_run_endpoint_starts_the_active_trips_run(client, trip, fake_ai, run_now):
    activate(client, trip)
    r = client.post(reverse("core:ai_run"))
    assert r.status_code == 200
    assert r.json()["status"] == "running"
    assert client.get(reverse("core:ai_status")).json() == {"status": "done", "up_to_date": True, "error": ""}


def test_run_endpoint_retry_flag_repeats_a_failed_run(client, trip, fake_ai, run_now):
    activate(client, trip)
    fake_ai.fail = ConnectionError("down")
    client.post(reverse("core:ai_run"))
    fake_ai.fail = None
    client.post(reverse("core:ai_run"))
    assert client.get(reverse("core:ai_status")).json()["status"] == "failed"
    client.post(reverse("core:ai_run"), {"retry": "1"})
    assert client.get(reverse("core:ai_status")).json()["status"] == "done"


@pytest.mark.django_db
@pytest.mark.parametrize("name", ["core:ai_run", "core:ai_status"])
def test_endpoints_need_an_active_trip(client, name):
    r = client.post(reverse(name)) if name == "core:ai_run" else client.get(reverse(name))
    assert r.status_code == 400
    assert r.json()["status"] == "no_trip"


@pytest.mark.django_db
def test_run_endpoint_only_accepts_post(client):
    assert client.get(reverse("core:ai_run")).status_code == 405


def test_activities_appear_on_the_ai_page_after_a_run(client, trip, fake_ai, run_now):
    activate(client, trip)
    ai_runner.start(trip)
    html = client.get(reverse("core:ai_output")).content.decode()
    acts = html[html.index('id="ai-activities"'):]
    acts = acts[:acts.index("</section>")]
    assert "Live music, Sixth Street" in acts
    assert "A mix of outdoors and nightlife." in acts


def test_summary_page_starts_the_ai_only_when_the_trip_has_members(client, trip):
    activate(client, trip)
    assert reverse("core:ai_run") in client.get(reverse("core:summary")).content.decode()

    empty = Trip.objects.create(name="Empty")
    activate(client, empty)
    assert reverse("core:ai_run") not in client.get(reverse("core:summary")).content.decode()


def test_viewing_the_pages_never_calls_the_ai_directly(client, trip, monkeypatch):
    """Pages only render; the AI starts from the browser's request to the run endpoint."""
    def boom(*args, **kwargs):
        raise AssertionError("rendering a page must not call the model")

    monkeypatch.setattr(ollama, "chat", boom)
    activate(client, trip)
    assert client.get(reverse("core:summary")).status_code == 200
    assert client.get(reverse("core:ai_output")).status_code == 200