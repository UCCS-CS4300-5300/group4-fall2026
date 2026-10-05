"""Submission form (Andrew): validation, and saving into the database."""
import pytest

REQUIRED_FIELDS = ["destinations", "availableDates", "budget"]  # the MVP inputs


def test_valid_submission_is_accepted(submission_form_cls, valid_submission):
    form = submission_form_cls(data=valid_submission)
    assert form.is_valid(), form.errors


@pytest.mark.parametrize("field", REQUIRED_FIELDS)
def test_mvp_fields_are_required(submission_form_cls, valid_submission, field):
    del valid_submission[field]
    form = submission_form_cls(data=valid_submission)
    assert not form.is_valid()
    assert field in form.errors


def test_activities_are_optional(submission_form_cls, valid_submission):
    valid_submission["activities"] = ""
    form = submission_form_cls(data=valid_submission)
    assert form.is_valid(), form.errors


def test_malformed_date_is_rejected(submission_form_cls, valid_submission):
    valid_submission["availableDates"] = "next tuesday"
    form = submission_form_cls(data=valid_submission)
    assert not form.is_valid()
    assert "availableDates" in form.errors


@pytest.mark.parametrize("budget", ["-50", "abc"])
def test_bad_budget_is_rejected(submission_form_cls, valid_submission, budget):
    valid_submission["budget"] = budget
    form = submission_form_cls(data=valid_submission)
    assert not form.is_valid()
    assert "budget" in form.errors


@pytest.mark.django_db
def test_saved_submission_matches_input(
    submission_form_cls, user_model, valid_submission, expected_user_data
):
    form = submission_form_cls(data=valid_submission)
    assert form.is_valid(), form.errors
    saved = form.save()

    stored = user_model.objects.get(pk=saved.pk)
    for field, expected in expected_user_data.items():
        assert getattr(stored, field) == expected, field
