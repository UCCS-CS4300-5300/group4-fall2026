"""AI caller (Joe). The model is always mocked: no network, no API cost."""
import pytest


@pytest.fixture(autouse=True)
def fake_model(monkeypatch, ai):
    """Replace call_model for every test here so nothing reaches the real API."""
    def fake(prompt):
        fake.prompts.append(prompt)
        return fake.reply

    fake.prompts = []
    fake.reply = "Austin"
    monkeypatch.setattr(ai, "call_model", fake)
    return fake


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


def test_model_is_called_once_with_the_built_prompt(ai, fake_model, trip_with_users):
    expected = ai.build_prompt(trip_with_users)
    ai.suggest_destination(trip_with_users)
    assert fake_model.prompts == [expected]


def test_reply_is_returned_without_whitespace(ai, fake_model, trip_with_users):
    fake_model.reply = "  Austin\n"
    assert ai.suggest_destination(trip_with_users) == "Austin"


def test_result_is_saved_on_the_trip(ai, trip_with_users):
    ai.suggest_destination(trip_with_users)
    trip_with_users.refresh_from_db()
    assert trip_with_users.suggested_destination == "Austin"


def test_blank_reply_raises(ai, fake_model, trip_with_users):
    fake_model.reply = "   "
    with pytest.raises(ValueError):
        ai.suggest_destination(trip_with_users)


@pytest.mark.django_db
def test_trip_without_users_never_calls_model(ai, fake_model, trip_model):
    empty = trip_model.objects.create(name="Empty")
    with pytest.raises(ValueError):
        ai.suggest_destination(empty)
    assert fake_model.prompts == []
