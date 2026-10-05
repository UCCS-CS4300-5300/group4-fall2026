"""
AI caller (Joe). The model is always mocked: tests never need Ollama running.

Joe's prompt asks the model to put the destination in bold, like
**Austin, Texas, USA**, followed by a paragraph explaining the choice.
"""
import pytest

GOOD_REPLY = "**Austin, Texas, USA**\nAustin fits everyone's budget and overlaps most picks."


@pytest.fixture(autouse=True)
def fake_model(monkeypatch, ai):
    """Replace call_model for every test here so nothing reaches the real model."""
    def fake(prompt):
        fake.prompts.append(prompt)
        return fake.reply

    fake.prompts = []
    fake.reply = GOOD_REPLY
    monkeypatch.setattr(ai, "call_model", fake)
    return fake


# ---- Building the prompt ----------------------------------------------------

def test_prompt_is_nonempty_text(ai, trip_with_users):
    prompt = ai.build_prompt(trip_with_users)
    assert isinstance(prompt, str) and prompt.strip()


def test_prompt_includes_every_users_destinations(ai, trip_with_users, users_of):
    prompt = ai.build_prompt(trip_with_users)
    for user in users_of(trip_with_users).all():
        for place in user.destinations:
            assert place in prompt


def test_prompt_includes_every_users_budget(ai, trip_with_users, users_of):
    prompt = ai.build_prompt(trip_with_users)
    for user in users_of(trip_with_users).all():
        assert str(int(user.budget)) in prompt


def test_prompt_keeps_users_anonymous(ai, trip_with_users, users_of):
    """Names are internal identifiers only; they must never be sent to the AI."""
    prompt = ai.build_prompt(trip_with_users)
    for user in users_of(trip_with_users).all():
        assert user.name not in prompt


# ---- Calling the model and reading its reply --------------------------------

def test_model_is_called_once_with_the_built_prompt(ai, fake_model, trip_with_users):
    expected = ai.build_prompt(trip_with_users)
    ai.suggest_destination(trip_with_users)
    assert fake_model.prompts == [expected]


@pytest.mark.parametrize("reply", [
    GOOD_REPLY,
    "Here's my pick: ** Austin ,  Texas , USA ** because it works for everyone.",
])
def test_destination_is_parsed_from_reply(ai, fake_model, trip_with_users, reply):
    fake_model.reply = reply
    assert ai.suggest_destination(trip_with_users) == "Austin, Texas, USA"


def test_full_reply_is_saved_on_the_trip(ai, fake_model, trip_with_users, ai_field):
    ai.suggest_destination(trip_with_users)
    trip_with_users.refresh_from_db()
    assert getattr(trip_with_users, ai_field) == GOOD_REPLY


@pytest.mark.parametrize("reply", ["", "   ", "I'd suggest Austin, Texas."])
def test_reply_without_bold_destination_raises_value_error(
    ai, fake_model, trip_with_users, reply
):
    """Models don't always follow the format; that should be a clear error, not a crash."""
    fake_model.reply = reply
    with pytest.raises(ValueError):
        ai.suggest_destination(trip_with_users)


@pytest.mark.django_db
def test_trip_without_users_never_calls_model(ai, fake_model, trip_model):
    empty = trip_model.objects.create(name="Empty")
    with pytest.raises(ValueError):
        ai.suggest_destination(empty)
    assert fake_model.prompts == []
