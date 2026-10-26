# Sprint 1 starter tests

This folder goes in `project/tests/`, next to `manage.py`. Run from `project/`:

    pip install -r requirements.txt
    pytest

Tests skip until the code they cover exists, so CI stays green while pieces
are still being written. If your names differ from the ones below, tell
Joseph or edit the constants at the top of `tests/conftest.py`.

## What each piece is expected to provide (app: `core`)

**User (Roy)**: `core/models.py` → `User`. Already written on `user_object_branch`.
The tests add DB-persistence checks on top of Roy's in-memory tests in `core/tests.py`.

**Form (Andrew)**: `core/forms.py` → `SubmissionForm`, a ModelForm that saves a `User`
- Fields: `destinations`, `availableDates`, `budget`, `activities`
- NOTE: `User.availableDates` was replaced by `DateRange` (`user.available_ranges`) in Sprint 2.
  The form tests still use the old field and skip until a form exists; update them with the form.
- Assumed input: comma-separated text, e.g. `"Denver, Austin"` and `"2026-12-18, 2026-12-19"`,
  stored as lists. Dates stored as `YYYY-MM-DD` strings, same as Roy's tests.
- Required: everything except `activities` (the model allows blanks; the form enforces the MVP)
- Rejects: malformed dates, negative or non-numeric budget

**Trip (Evan)**: `core/models/trip.py` → `Trip`. On `sprint-1`.
- `users` must be a ManyToManyField to `core.User` (Roy's model), not `settings.AUTH_USER_MODEL`
- `ai_output` holds the AI's full reply

**AI caller (Joe)**: `core/ai.py` (an importable module; the current script lives in a folder with spaces)
- `build_prompt(trip) -> str` includes every user's destinations and budget, and never their names
- `call_model(prompt) -> str` is the only function that talks to Ollama (tests replace it)
- `suggest_destination(trip) -> str` calls the model once, saves the full reply to `trip.ai_output`,
  and returns the bolded destination as `"City, State, Country"`
- Raises `ValueError` if the reply has no `**...**` destination, or if the trip has no users
  (without calling the model)
