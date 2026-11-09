"""
Runs a trip's AI in the background so no page waits on the model.

One run asks for the destination (Trip.AIDest), then activities for that
destination (Trip.AIGetAct), then a budget check for that plan
(Trip.AIGetBudget). A run starts only when the trip's answers have
changed since the last one, so the slow model is called as few times as
possible. Pages start a run and then poll its state.
"""
import hashlib
import json
import logging
import threading
from datetime import timedelta

from django.db import connections, transaction
from django.utils import timezone

from .models import AIParser, AIRun
from .models.trip import AISuggestion

log = logging.getLogger(__name__)

# A run still "running" after this long is treated as lost (e.g. the server restarted).
STALE_AFTER = timedelta(minutes=10)

# Only one request at a time may decide whether to start a run.
_start_lock = threading.Lock()


def inputs_key(trip):
    """A fingerprint of every member's answers. It changes whenever any answer changes."""
    members = trip.users.prefetch_related("available_ranges").order_by("pk")
    data = [
        [
            m.pk,
            m.destinations,
            m.activities,
            str(m.budget),
            sorted(
                [r.startDate.isoformat(), r.endDate.isoformat()] for r in m.available_ranges.all()
            ),
        ]
        for m in members
    ]
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()


def _is_stale(run):
    return run.started_at is None or timezone.now() - run.started_at > STALE_AFTER


def state(trip):
    """
    What the pages show, as a dict:
    status is idle, running, done or failed; up_to_date says whether the
    saved results match the members' current answers; error explains a failure.
    """
    run = AIRun.objects.filter(trip=trip).first()
    if run is None:
        return {"status": AIRun.IDLE, "up_to_date": False, "error": ""}
    status, error = run.status, run.error
    if status == AIRun.RUNNING and _is_stale(run):
        status, error = AIRun.FAILED, "The last run did not finish."
    return {"status": status, "up_to_date": run.inputs == inputs_key(trip), "error": error}


def start(trip, retry=False):
    """
    Start a background run unless one is already running or the saved results
    already match the members' answers. A failed run is only repeated for the
    same answers when retry is True. Returns the state after deciding.
    """
    if not trip.users.exists():
        return {
            "status": AIRun.IDLE,
            "up_to_date": False,
            "error": "No one has joined this trip yet.",
        }

    key = inputs_key(trip)
    with _start_lock, transaction.atomic():
        run, _ = AIRun.objects.select_for_update().get_or_create(trip=trip)
        if run.status == AIRun.RUNNING and not _is_stale(run):
            return state(trip)
        if run.inputs == key and run.status == AIRun.DONE:
            return state(trip)
        if run.inputs == key and run.status == AIRun.FAILED and not retry:
            return state(trip)
        run.status = AIRun.RUNNING
        run.inputs = key
        run.error = ""
        run.started_at = timezone.now()
        run.finished_at = None
        run.save()

    launch(run.pk)  # after the atomic block, so the thread sees the saved run
    return {"status": AIRun.RUNNING, "up_to_date": True, "error": ""}


def launch(run_id):
    """Run in a background thread. Tests replace this to run synchronously."""

    def work():
        try:
            run_ai(run_id)
        finally:
            connections.close_all()  # this thread's own database connection

    threading.Thread(target=work, daemon=True, name=f"trip-ai-run-{run_id}").start()


def _reason(exc):
    """A short message for the page; the full error goes to the server log."""
    if isinstance(exc, ValueError) and "destination" in str(exc).lower():
        return "Add at least one destination before asking the AI."
    if isinstance(exc, IndexError):
        return "The AI's reply wasn't in the expected format. Try again."
    return "The AI service isn't available right now."


def _explanation(raw):
    """
    The AI's reasoning without the **bold** answer it starts with, which the
    page already shows in the short box. Falls back to the whole reply.
    """
    text = raw.rsplit("**", 1)[-1].strip() if raw.count("**") >= 2 else ""
    return text or raw.replace("**", "").strip()


def _budget_short(amount):
    """'1450' -> '$1,450 estimated total'; anything unparseable is shown as the AI wrote it."""
    try:
        return f"${float(amount):,.0f} estimated total"
    except (TypeError, ValueError):
        return str(amount).strip()


def _budget_result(trip, location, activities):
    """
    The AI's budget check for the plan, or None when no one gave a budget.
    A failure here is logged and skipped, so it never discards the
    destination and activities already generated.
    """
    if trip.get_avg_budget() == "IGNORE":
        return None
    try:
        budget = trip.AIGetBudget(AIParser(), location, activities)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        log.warning("Budget step for trip %s failed: %r", trip.pk, exc)
        return None
    return {"short": _budget_short(budget["Budget"]), "long": _explanation(budget["Raw"])}


def run_ai(run_id):
    """Call the AI for the run's trip and save what it returns. Never raises."""
    run = AIRun.objects.select_related("trip").get(pk=run_id)
    trip = run.trip
    try:
        dest = trip.AIDest(AIParser())
        location = dest["Location"].strip()
        AISuggestion.objects.create(
            trip=trip, location=location, description=_explanation(dest["Raw"])
        )

        results = {}
        try:
            acts = trip.AIGetAct(AIParser(), location)
        except ValueError:
            acts = None  # no member listed any activities, so there is nothing to suggest
        activities = []
        if acts:
            activities = [a.strip() for a in acts["Activities"] if a.strip()]
            results["activities"] = {
                "short": ", ".join(activities),
                "long": _explanation(acts["Raw"]),
            }

        budget = _budget_result(trip, location, activities)
        if budget:
            results["budget"] = budget

        run.results = results
        run.status = AIRun.DONE
    except Exception as exc:  # pylint: disable=broad-exception-caught
        # Any failure (Ollama not running, a bad reply) must end the run, not leave it "running".
        log.warning("AI run %s for trip %s failed: %r", run_id, trip.pk, exc)
        run.status = AIRun.FAILED
        run.error = _reason(exc)
    run.finished_at = timezone.now()
    run.save()
