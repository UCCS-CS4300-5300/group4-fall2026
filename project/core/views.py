from django.shortcuts import redirect, render
from .models import StarterItem, User
from .models.trip import AISuggestion
from .summary import build_group_summary


def home(request):
    if request.method == "POST":
        trip_name = request.POST.get("tripName", "").strip()
        person_name = request.POST.get("personName", "").strip()

        if not trip_name or not person_name:
            return render(
                request,
                "core/home.html",
                {"error": "Please enter both your trip name and your name."},
                status=400,
            )

        request.session["trip_name"] = trip_name
        request.session["person_name"] = person_name

        return redirect("core:destination")

    items = StarterItem.objects.filter(
        is_active=True
    ).order_by("title")

    return render(request, 
    	"core/home.html", 
    	{"items": items}
    )


def destination(request):
    print("DESTINATION VIEW:", request.method)

    if request.method == "POST":
        destinations = request.POST.getlist("destinations")
        print("DESTINATIONS RECEIVED:", destinations)

        if not destinations:
            print("ERROR: NO DESTINATIONS RECEIVED")
            return render(
                request,
                "core/destination.html",
                {
                    "items": StarterItem.objects.filter(
                        is_active=True
                    ).order_by("title"),
                    "trip_name": request.session.get("trip_name", ""),
                    "person_name": request.session.get("person_name", ""),
                    "error": "Please add at least one destination.",
                },
                status=400,
            )

        request.session["trip_destinations"] = destinations
        print("REDIRECTING TO SCHEDULE")

        return redirect("core:schedule")

    return render(
        request,
        "core/destination.html",
        {
            "items": StarterItem.objects.filter(
                is_active=True
            ).order_by("title"),
            "trip_name": request.session.get("trip_name", ""),
            "person_name": request.session.get("person_name", ""),
        },
    )


def schedule(request):
    if request.method == "POST":
        request.session["trip_schedule"] = {
            "start_date": request.POST.get("start_date", ""),
            "end_date": request.POST.get("end_date", ""),
            "pace": request.POST.get("pace", "balanced"),
            "day_start": request.POST.get("day_start", "09:00"),
            "day_end": request.POST.get("day_end", "21:00"),
        }

        return redirect("core:budget")

    return render(request, "core/schedule.html")




def budget(request):
    if request.method == "POST":
        budget_amount = request.POST.get("budget_amount", "").strip()
        currency = request.POST.get("currency", "USD").strip()

        # Validate the budget before saving it.
        from decimal import Decimal, InvalidOperation

        try:
            amount = Decimal(budget_amount)
            if not amount.is_finite() or amount <= 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            return render(
                request,
                "core/budget.html",
                {"error": "Please enter a valid budget greater than zero."},
                status=400,
            )

        allowed_currencies = {"USD", "EUR", "GBP", "CAD", "AUD", "JPY"}
        if currency not in allowed_currencies:
            currency = "USD"

        # Save the budget for the trip-planning step.
        request.session["trip_budget"] = {
            "amount": str(amount),
            "currency": currency,
        }

        return redirect("core:activities")

    return render(request, "core/budget.html")




def activities(request):
    if request.method == "POST":
        # Retrieve the selected activity checkboxes.
        activities = request.POST.getlist("activities")

        # Retrieve the optional text field.
        additional_notes = request.POST.get(
            "additional_notes", ""
        ).strip()

        # Store the answers for the next step.
        request.session["trip_activities"] = activities
        request.session["trip_additional_notes"] = additional_notes

        # Continue to the existing summary page for now.
        return redirect("core:summary")

    return render(request, "core/activities.html")




def summary(request):
    trip_data = {
        "destinations": request.session.get("trip_destinations", []),
        "schedule": request.session.get("trip_schedule", {}),
        "budget": request.session.get("trip_budget", {}),
        "activities": request.session.get("trip_activities", []),
        "additional_notes": request.session.get(
            "trip_additional_notes", ""
        ),
    }

    return render(
        request,
        "core/summary.html",
        {
            "summary": build_group_summary(User.objects.all()),
            "trip_data": trip_data,
        },
    )



def ai_output(request):
    """
    PLACEHOLDER for testing: lists saved AI suggestions, newest first.
    Nothing here calls the model; it only shows what is already stored.
    """
    suggestions = AISuggestion.objects.select_related("trip").order_by("-created_at", "-id")
    return render(request, "core/ai_output.html", {"suggestions": suggestions})
