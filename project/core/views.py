from django.shortcuts import render, redirect
from .models import StarterItem, User
from .models.trip import AISuggestion
from .summary import build_group_summary


def destination(request):
    if request.method == "POST":
        destinations = request.POST.getlist("destinations")

        print("DESTINATIONS:", destinations)

        request.session["trip_destinations"] = destinations

        return redirect("schedule")

    return render(
        request,
        "core/destination.html",
        {
            "items": StarterItem.objects.filter(
                is_active=True
            ).order_by("title")
        }
    )


def schedule(request):
    return render(request, "core/schedule.html")


def summary(request):
    """Anonymous overview of every member's preferences currently saved."""
    return render(
        request,
        "core/summary.html",
        {"summary": build_group_summary(User.objects.prefetch_related("available_ranges"))},
    )


def ai_output(request):
    """
    PLACEHOLDER for testing: lists saved AI suggestions, newest first.
    Nothing here calls the model; it only shows what is already stored.
    """
    suggestions = AISuggestion.objects.select_related("trip").order_by("-created_at", "-id")
    return render(request, "core/ai_output.html", {"suggestions": suggestions})
