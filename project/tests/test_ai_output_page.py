"""AI suggestions page (Joseph): the trip's saved results in three sections; never calls the model."""
import pytest
from django.urls import reverse

from core.models import Trip, User
from core.models.trip import AISuggestion


@pytest.fixture
def trip(db):
    trip = Trip.objects.create(name="Winter break")
    trip.add_user(User.objects.create(name="Quentin", destinations=["Austin"]))
    return trip


@pytest.fixture
def page(client, log_in):
    """page(trip) returns the AI page's HTML as the trip's first member."""
    def _page(trip):
        log_in(trip, trip.users.order_by("pk").first())
        return client.get(reverse("core:ai_output")).content.decode()

    return _page


def section(html, key):
    """The HTML of one section (destination, activities or budget)."""
    start = html.index(f'id="ai-{key}"')
    end = html.find("</section>", start)
    return html[start:end]


@pytest.mark.django_db
def test_without_signing_in_the_page_redirects_to_the_start(client):
    r = client.get(reverse("core:ai_output"))
    assert r.status_code == 302 and r.url == reverse("core:home")


def test_page_has_destination_activities_and_budget_sections_in_order(trip, page):
    html = page(trip)
    assert "Winter break" in html
    positions = [html.index(f'id="ai-{key}"') for key in ("destination", "activities", "budget")]
    assert positions == sorted(positions)


def test_destination_shows_short_answer_and_explanation(trip, page):
    AISuggestion.objects.create(
        trip=trip, location="Austin, Texas, USA", description="Austin overlaps most picks."
    )
    dest = section(page(trip), "destination")
    assert "Austin, Texas, USA" in dest
    assert "Austin overlaps most picks." in dest
    assert "not been generated" not in dest


def test_newest_destination_is_shown(trip, page):
    AISuggestion.objects.create(trip=trip, location="Denver, Colorado, USA", description="Older.")
    AISuggestion.objects.create(trip=trip, location="Austin, Texas, USA", description="Newer.")
    dest = section(page(trip), "destination")
    assert "Austin, Texas, USA" in dest and "Denver" not in dest


def test_other_trips_suggestions_are_not_shown(trip, page):
    other = Trip.objects.create(name="Spring break")
    AISuggestion.objects.create(trip=other, location="Miami, Florida, USA", description="Beach.")
    html = page(trip)
    assert "Miami" not in html
    assert "not been generated" in section(html, "destination")


def test_parts_not_generated_yet_say_so(trip, page):
    AISuggestion.objects.create(trip=trip, location="Austin, Texas, USA", description="Why.")
    html = page(trip)
    assert "not been generated" in section(html, "activities")
    assert "not been generated" in section(html, "budget")


def test_page_does_not_call_the_ai(trip, page, monkeypatch):
    """Viewing the page only reads saved results; it must never reach Ollama."""
    import ollama

    def boom(*args, **kwargs):
        raise AssertionError("the AI suggestions page should not call the model")

    monkeypatch.setattr(ollama, "chat", boom)
    assert "Winter break" in page(trip)


def test_suggestion_text_is_escaped(trip, page):
    """Model output is untrusted text; it must not be rendered as HTML."""
    AISuggestion.objects.create(trip=trip, location="<b>Austin</b>", description="<script>alert(1)</script>")
    html = page(trip)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_page_shows_progress_and_reloads_when_done(trip, page):
    html = page(trip)
    assert reverse("core:ai_run") in html and reverse("core:ai_status") in html
    assert 'data-reload="1"' in html


def test_page_links_back_to_summary(trip, page):
    assert f'href="{reverse("core:summary")}"' in page(trip)
