from django.shortcuts import render, redirect
from .models import StarterItem


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
