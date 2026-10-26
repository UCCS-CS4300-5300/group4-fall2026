"""AI output placeholder page (Joseph): shows stored AISuggestion rows, never calls the model."""
import pytest
from django.urls import reverse

from core.models import Trip
from core.models.trip import AISuggestion


@pytest.mark.django_db
def test_empty_state_when_no_suggestions(client):
    r = client.get(reverse("core:ai_output"))
    assert r.status_code == 200
    assert "No AI suggestions yet" in r.content.decode()


@pytest.mark.django_db
def test_saved_suggestions_are_shown_newest_first(client):
    trip = Trip.objects.create(name="Winter break")
    AISuggestion.objects.create(trip=trip, location="Denver, Colorado, USA", description="Skiing nearby.")
    AISuggestion.objects.create(trip=trip, location="Austin, Texas, USA", description="Fits every budget.")

    html = client.get(reverse("core:ai_output")).content.decode()
    assert "Winter break" in html
    assert "Fits every budget." in html
    assert html.index("Austin, Texas, USA") < html.index("Denver, Colorado, USA")


@pytest.mark.django_db
def test_page_does_not_call_the_ai(client, monkeypatch):
    """It's a placeholder: viewing it must never reach Ollama."""
    import ollama

    def boom(*args, **kwargs):
        raise AssertionError("the AI output page should not call the model")

    monkeypatch.setattr(ollama, "chat", boom)
    assert client.get(reverse("core:ai_output")).status_code == 200


@pytest.mark.django_db
def test_suggestion_text_is_escaped(client):
    """Model output is untrusted text; it must not be rendered as HTML."""
    trip = Trip.objects.create(name="Test")
    AISuggestion.objects.create(trip=trip, location="<b>Austin</b>", description="<script>alert(1)</script>")
    html = client.get(reverse("core:ai_output")).content.decode()
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
