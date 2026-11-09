
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET, require_POST

from . import ai_runner

from .models import (
    AIRun,
    StarterItem,
    Trip,
    User,
    DateRange,
)

from .summary import build_group_summary


# --------------------------------------------------
# SESSION HELPERS
# --------------------------------------------------

ACTIVE_TRIP_KEY = "active_trip_id"
ACTIVE_USER_KEY = "active_user_id"


def active_trip(request):
    trip_id = request.session.get(ACTIVE_TRIP_KEY)

    if not trip_id:
        return None

    return Trip.objects.filter(pk=trip_id).first()


def active_user(request):
    trip = active_trip(request)

    user_id = request.session.get(ACTIVE_USER_KEY)

    if trip is None or user_id is None:
        return None

    # Only return a participant belonging to this trip.
    return trip.users.filter(pk=user_id).first()


def require_participant(request):
    trip = active_trip(request)
    user = active_user(request)

    if trip is None or user is None:
        return None, None

    return trip, user


def participant_context(trip, user):
    return {
        "trip": trip,
        "trip_name": trip.name,
        "person_name": user.name,
        "invite_code": trip.invite_code,
        "user": user,
    }


def home_context(error=None):
    context = {
        "items": StarterItem.objects.filter(
            is_active=True
        ).order_by("title")
    }

    if error:
        context["error"] = error

    return context


# --------------------------------------------------
# CREATE TRIP
# --------------------------------------------------

def home(request):

    if request.method == "POST":

        trip_name = request.POST.get(
            "tripName", ""
        ).strip()

        person_name = request.POST.get(
            "personName", ""
        ).strip()

        if not trip_name or not person_name:
            return render(
                request,
                "core/home.html",
                home_context(
                    "Please enter both your trip name and your name."
                ),
                status=400,
            )

        if len(trip_name) > 120 or len(person_name) > 50:
            return render(
                request,
                "core/home.html",
                home_context("One of the entered names is too long."),
                status=400,
            )

        with transaction.atomic():

            trip = Trip.objects.create(
                name=trip_name
            )

            user = User.objects.create(
                name=person_name
            )

            trip.users.add(user)

        # This browser now belongs to the new trip.
        request.session.cycle_key()

        request.session[ACTIVE_TRIP_KEY] = trip.id
        request.session[ACTIVE_USER_KEY] = user.id

        return redirect("core:destination")

    return render(
        request,
        "core/home.html",
        home_context()
    )


# --------------------------------------------------
# JOIN EXISTING TRIP
# --------------------------------------------------

def join_trip(request):
    """
    Join a trip with its invitation code. A shared link (/join/?code=ABC12345)
    fills the code in. Joining again with the same name (any capitalization)
    continues as that member instead of adding a duplicate.
    """

    if request.method == "POST":

        invite_code = request.POST.get(
            "invite_code", ""
        ).strip().upper()

        person_name = request.POST.get(
            "person_name", ""
        ).strip()

        def error(message):
            # Keep what was typed so the person only fixes the mistake.
            return render(
                request,
                "core/join_trip.html",
                {
                    "error": message,
                    "invite_code": invite_code,
                    "person_name": person_name,
                },
                status=400,
            )

        if not invite_code or not person_name:
            return error("Please enter your name and invitation code.")

        if len(person_name) > 50:
            return error("Your name must be 50 characters or fewer.")

        trip = Trip.objects.filter(
            invite_code=invite_code
        ).first()

        if trip is None:
            return error("Invalid invitation code.")

        with transaction.atomic():

            user = trip.users.filter(
                name__iexact=person_name
            ).order_by("pk").first()

            if user is None:
                user = User.objects.create(
                    name=person_name
                )

                trip.users.add(user)

        # Start a fresh participant session.
        request.session.cycle_key()

        request.session[ACTIVE_TRIP_KEY] = trip.id
        request.session[ACTIVE_USER_KEY] = user.id

        return redirect("core:destination")

    return render(
        request,
        "core/join_trip.html",
        {
            "invite_code": request.GET.get("code", "").strip().upper()[:8],
        },
    )


# --------------------------------------------------
# DESTINATIONS
# --------------------------------------------------

def destination(request):

    trip, user = require_participant(request)

    if trip is None:
        return redirect("core:home")

    if request.method == "POST":

        destinations = request.POST.getlist(
            "destinations"
        )

        # Normalize and remove duplicate entries.
        normalized = []
        seen = set()

        for destination_name in destinations:

            name = " ".join(destination_name.split())
            key = name.casefold()

            if name and key not in seen:
                normalized.append(name)
                seen.add(key)

        if not normalized:
            context = participant_context(trip, user)
            context["error"] = "Please add at least one destination."

            return render(
                request,
                "core/destination.html",
                context,
                status=400,
            )

        user.destinations = normalized

        user.save(
            update_fields=["destinations"]
        )

        return redirect("core:schedule")

    context = participant_context(trip, user)

    context["existing_destinations"] = user.destinations

    return render(
        request,
        "core/destination.html",
        context
    )


# --------------------------------------------------
# SCHEDULE AND AVAILABILITY
# --------------------------------------------------

def schedule(request):

    trip, user = require_participant(request)

    if trip is None:
        return redirect("core:home")

    if request.method == "POST":

        start_value = request.POST.get("start_date", "")
        end_value = request.POST.get("end_date", "")

        start_date = parse_date(start_value)
        end_date = parse_date(end_value)

        if not start_date or not end_date:
            context = participant_context(trip, user)
            context["error"] = "Please enter valid start and end dates."

            return render(
                request,
                "core/schedule.html",
                context,
                status=400,
            )

        if end_date < start_date:
            context = participant_context(trip, user)
            context["error"] = "The end date must be after the start date."

            return render(
                request,
                "core/schedule.html",
                context,
                status=400,
            )

        if (end_date - start_date).days > 365:
            context = participant_context(trip, user)
            context["error"] = "Your availability cannot exceed 366 days."

            return render(
                request,
                "core/schedule.html",
                context,
                status=400,
            )

        pace = request.POST.get("pace", "balanced")

        if pace not in {"relaxed", "balanced", "packed"}:
            pace = "balanced"

        day_start = request.POST.get("day_start", "09:00")
        day_end = request.POST.get("day_end", "21:00")

        # Save the availability for this participant only.
        with transaction.atomic():

            user.available_ranges.all().delete()

            DateRange.objects.create(
                user=user,
                startDate=start_date,
                endDate=end_date,
            )

            user.schedule_preferences = {
                "pace": pace,
                "day_start": day_start,
                "day_end": day_end,
            }

            user.save(
                update_fields=["schedule_preferences"]
            )

        return redirect("core:budget")

    context = participant_context(trip, user)

    return render(
        request,
        "core/schedule.html",
        context
    )


# --------------------------------------------------
# BUDGET
# --------------------------------------------------

def budget(request):

    trip, user = require_participant(request)

    if trip is None:
        return redirect("core:home")

    if request.method == "POST":

        budget_amount = request.POST.get(
            "budget_amount", ""
        ).strip()

        currency = request.POST.get(
            "currency", "USD"
        ).strip().upper()

        try:

            amount = Decimal(budget_amount)

            if (
                not amount.is_finite()
                or amount <= 0
                or amount > Decimal("9999999999.99")
            ):
                raise InvalidOperation

        except (InvalidOperation, ValueError):

            context = participant_context(trip, user)
            context["error"] = "Please enter a valid budget greater than zero."

            return render(
                request,
                "core/budget.html",
                context,
                status=400,
            )

        allowed_currencies = {
            "USD", "EUR", "GBP", "CAD", "AUD", "JPY"
        }

        if currency not in allowed_currencies:
            currency = "USD"

        user.budget = amount
        user.currency = currency

        user.save(
            update_fields=["budget", "currency"]
        )

        return redirect("core:activities")

    context = participant_context(trip, user)

    return render(
        request,
        "core/budget.html",
        context
    )


# --------------------------------------------------
# ACTIVITIES
# --------------------------------------------------

def activities(request):

    trip, user = require_participant(request)

    if trip is None:
        return redirect("core:home")

    if request.method == "POST":

        selected_activities = request.POST.getlist(
            "activities"
        )

        additional_notes = request.POST.get(
            "additional_notes", ""
        ).strip()

        if len(additional_notes) > 5000:
            context = participant_context(trip, user)
            context["error"] = "Your notes are too long."

            return render(
                request,
                "core/activities.html",
                context,
                status=400,
            )

        user.activities = list(dict.fromkeys(
            a.strip()
            for a in selected_activities
            if a.strip()
        ))

        user.additional_notes = additional_notes

        user.save(
            update_fields=[
                "activities",
                "additional_notes",
            ]
        )

        return redirect("core:summary")

    context = participant_context(trip, user)

    return render(
        request,
        "core/activities.html",
        context
    )


# --------------------------------------------------
# GROUP SUMMARY
# --------------------------------------------------

def summary(request):

    trip, user = require_participant(request)

    if trip is None:
        return redirect("core:home")

    members = trip.users.prefetch_related(
        "available_ranges"
    )

    group_summary = build_group_summary(members)

    # Additional group-wide information.
    group_summary["participants"] = trip.users.count()

    group_summary["submitted_preferences"] = {
        "destinations": trip.users.exclude(
            destinations=[]
        ).count(),

        "activities": trip.users.exclude(
            activities=[]
        ).count(),

        "budgets": trip.users.filter(
            budget__isnull=False
        ).count(),

        "availability": trip.users.filter(
            available_ranges__isnull=False
        ).distinct().count(),
    }

    context = participant_context(trip, user)

    context.update({
        "summary": group_summary,
        "members": trip.users.all(),
    })

    return render(
        request,
        "core/summary.html",
        context
    )


# --------------------------------------------------
# AI RESULTS
# --------------------------------------------------

AI_SECTIONS = [
    ("destination", "Destination", "Suggested destination"),
    ("activities", "Activities", "Suggested activities"),
    ("budget", "Budget", "Budget plan"),
]


def ai_results(trip):

    latest = trip.suggestions.order_by(
        "-created_at", "-id"
    ).first()

    run = AIRun.objects.filter(
        trip=trip
    ).first()

    extra = run.results if run else {}

    return {
        "destination": {
            "short": latest.location,
            "long": latest.description,
        } if latest else None,

        "activities": extra.get("activities"),

        "budget": extra.get("budget"),
    }


def ai_output(request):

    trip, user = require_participant(request)

    if trip is None:
        return redirect("core:home")

    results = ai_results(trip)

    sections = [
        {
            "key": key,
            "title": title,
            "short_label": label,
            "result": results[key],
        }
        for key, title, label in AI_SECTIONS
    ]

    context = participant_context(trip, user)

    context["sections"] = sections

    return render(
        request,
        "core/ai_output.html",
        context
    )


# --------------------------------------------------
# AI RUNNING
# --------------------------------------------------

def no_trip():
    return JsonResponse(
        {
            "status": "no_trip",
            "error": "No trip selected."
        },
        status=400,
    )


@require_POST
def ai_run(request):

    trip, user = require_participant(request)

    if trip is None:
        return no_trip()

    # The AI receives the whole trip, not just the
    # preferences of the current participant.
    return JsonResponse(
        ai_runner.start(
            trip,
            retry=request.POST.get("retry") == "1"
        )
    )


@require_GET
def ai_status(request):

    trip, user = require_participant(request)

    if trip is None:
        return no_trip()

    return JsonResponse(
        ai_runner.state(trip)
    )
