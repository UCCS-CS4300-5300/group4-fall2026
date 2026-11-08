"""AI suggestions page (Joseph): the active trip's saved results in three sections; never calls the model."""
import pytest
from django.urls import reverse

from core.models import Trip
from core.models.trip import AISuggestion


def activate(client, trip):
    """Make trip the active trip in client's session, as login does."""
    session = client.session
    session["active_trip_id"] = trip.pk
    session.save()


@pytest.fixture
def trip(client):
    """A trip that is already the active trip for the test client."""
    trip = Trip.objects.create(name="Winter break")
    activate(client, trip)
    return trip


def page(client):
    return client.get(reverse("core:ai_output")).content.decode()


def section(html, key):
    """The HTML of one section (destination, activities or budget)."""
    start = html.index(f'id="ai-{key}"')
    end = html.find("</section>", start)
    return html[start:end]


@pytest.mark.django_db
def test_without_an_active_trip_the_page_asks_to_start_or_join_one(client):
    r = client.get(reverse("core:ai_output"))
    html = r.content.decode()
    assert r.status_code == 200
    assert "No trip selected" in html
    assert f'href="{reverse("core:home")}"' in html


@pytest.mark.django_db
def test_page_has_destination_activities_and_budget_sections_in_order(client, trip):
    html = page(client)
    assert "Winter break" in html
    positions = [html.index(f'id="ai-{key}"') for key in ("destination", "activities", "budget")]
    assert positions == sorted(positions)


@pytest.mark.django_db
def test_destination_shows_short_answer_and_explanation(client, trip):
    AISuggestion.objects.create(
        trip=trip, location="Austin, Texas, USA", description="Austin overlaps most picks."
    )
    dest = section(page(client), "destination")
    assert "Austin, Texas, USA" in dest
    assert "Austin overlaps most picks." in dest
    assert "Not generated yet" not in dest


@pytest.mark.django_db
def test_newest_destination_is_shown(client, trip):
    AISuggestion.objects.create(trip=trip, location="Denver, Colorado, USA", description="Older.")
    AISuggestion.objects.create(trip=trip, location="Austin, Texas, USA", description="Newer.")
    dest = section(page(client), "destination")
    assert "Austin, Texas, USA" in dest and "Denver" not in dest


@pytest.mark.django_db
def test_other_trips_suggestions_are_not_shown(client, trip):
    other = Trip.objects.create(name="Spring break")
    AISuggestion.objects.create(trip=other, location="Miami, Florida, USA", description="Beach.")
    html = page(client)
    assert "Miami" not in html
    assert "Not generated yet" in section(html, "destination")


@pytest.mark.django_db
def test_parts_not_generated_yet_say_so(client, trip):
    AISuggestion.objects.create(trip=trip, location="Austin, Texas, USA", description="Why.")
    html = page(client)
    assert "Not generated yet" in section(html, "activities")
    assert "Not generated yet" in section(html, "budget")


@pytest.mark.django_db
def test_page_does_not_call_the_ai(client, trip, monkeypatch):
    """Viewing the page only reads saved results; it must never reach Ollama."""
    import ollama

    def boom(*args, **kwargs):
        raise AssertionError("the AI suggestions page should not call the model")

    monkeypatch.setattr(ollama, "chat", boom)
    assert client.get(reverse("core:ai_output")).status_code == 200


@pytest.mark.django_db
def test_suggestion_text_is_escaped(client, trip):
    """Model output is untrusted text; it must not be rendered as HTML."""
    AISuggestion.objects.create(trip=trip, location="<b>Austin</b>", description="<script>alert(1)</script>")
    html = page(client)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


@pytest.mark.django_db
def test_page_links_back_to_summary(client, trip):
    assert f'href="{reverse("core:summary")}"' in page(client)