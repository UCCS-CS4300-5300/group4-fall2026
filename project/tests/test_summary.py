"""Group summary (Joseph): combining everyone's preferences, and the summary page."""
import datetime as dt
from decimal import Decimal

import pytest
from django.urls import reverse

from core.models import User
from core.summary import build_group_summary

D1, D2, D3 = "2026-12-18", "2026-12-19", "2026-12-20"


def make(name, destinations=(), dates=(), budget=None, activities=()):
    return User.objects.create(
        name=name,
        destinations=list(destinations),
        availableDates=list(dates),
        budget=None if budget is None else Decimal(budget),
        activities=list(activities),
    )


# ---- Combining preferences --------------------------------------------------

@pytest.mark.django_db
def test_no_members_gives_empty_summary():
    s = build_group_summary(User.objects.all())
    assert s["member_count"] == 0
    assert s["destinations"] == [] and s["activities"] == []
    assert s["availability"]["responded"] == 0
    assert s["budget"]["responded"] == 0


@pytest.mark.django_db
def test_destinations_ranked_by_how_many_members_suggest_them():
    make("Quentin", ["Denver", "Austin"])
    make("Rosalind", ["Austin", "Chicago"])
    make("Thaddeus", ["Austin", "Denver"])
    s = build_group_summary(User.objects.all())
    assert s["destinations"] == [
        {"name": "Austin", "count": 3},
        {"name": "Denver", "count": 2},
        {"name": "Chicago", "count": 1},
    ]


@pytest.mark.django_db
def test_matching_ignores_case_and_spacing_and_counts_each_member_once():
    make("Quentin", ["Denver", "  denver "], activities=["Live Music"])
    make("Rosalind", ["DENVER"], activities=["live  music"])
    s = build_group_summary(User.objects.all())
    assert s["destinations"] == [{"name": "Denver", "count": 2}]
    assert s["activities"] == [{"name": "Live Music", "count": 2}]


@pytest.mark.django_db
def test_common_dates_are_the_ones_everyone_is_free():
    make("Quentin", dates=[D1, D2, D3])
    make("Rosalind", dates=[D2, D3])
    make("Thaddeus", dates=[D3, D2])
    a = build_group_summary(User.objects.all())["availability"]
    assert a["responded"] == 3
    assert a["common"] == [dt.date(2026, 12, 19), dt.date(2026, 12, 20)]


@pytest.mark.django_db
def test_without_a_common_date_the_best_dates_are_listed():
    make("Quentin", dates=[D1, D2])
    make("Rosalind", dates=[D2])
    make("Thaddeus", dates=[D3])
    a = build_group_summary(User.objects.all())["availability"]
    assert a["common"] == []
    assert a["best"][0] == {"date": dt.date(2026, 12, 19), "count": 2}


@pytest.mark.django_db
def test_members_without_dates_and_bad_dates_are_ignored():
    make("Quentin", dates=[D1, "next tuesday"])
    make("Rosalind", dates=[D1])
    make("Thaddeus")  # no dates yet; shouldn't wipe out the overlap
    a = build_group_summary(User.objects.all())["availability"]
    assert a["responded"] == 2
    assert a["common"] == [dt.date(2026, 12, 18)]


@pytest.mark.django_db
def test_budget_range_average_and_median():
    for name, budget in [("Quentin", "400"), ("Rosalind", "600"), ("Thaddeus", "800"), ("Ulrich", None)]:
        make(name, budget=budget)
    b = build_group_summary(User.objects.all())["budget"]
    assert b["responded"] == 3
    assert (b["min"], b["max"]) == (Decimal("400"), Decimal("800"))
    assert b["average"] == Decimal("600.00")
    assert b["median"] == Decimal("600.00")
    assert b["below"] == b["above"] == 0


@pytest.mark.django_db
def test_budget_outliers_are_counted_not_named():
    for name, budget in [("Quentin", "150"), ("Rosalind", "600"), ("Thaddeus", "650"), ("Ulrich", "2000")]:
        make(name, budget=budget)
    b = build_group_summary(User.objects.all())["budget"]
    assert (b["below"], b["above"]) == (1, 1)


@pytest.mark.django_db
def test_outliers_not_flagged_in_tiny_groups():
    """With two people, 'one budget is far lower' would reveal who it is."""
    make("Quentin", budget="100")
    make("Rosalind", budget="2000")
    b = build_group_summary(User.objects.all())["budget"]
    assert b["outliers_checked"] is False
    assert b["below"] == b["above"] == 0


# ---- The page ---------------------------------------------------------------

@pytest.mark.django_db
def test_summary_page_shows_combined_preferences(client):
    make("Quentin", ["Austin"], [D1], "500", ["Hiking"])
    make("Rosalind", ["Austin", "Miami"], [D1], "700", ["Beach"])
    r = client.get(reverse("summary"))
    html = r.content.decode()
    assert r.status_code == 200
    assert "2 members have submitted" in html
    for text in ["Austin", "Miami", "Hiking", "Beach", "Fri, Dec 18, 2026", "$500 – $700"]:
        assert text in html, text


@pytest.mark.django_db
def test_summary_page_never_shows_names(client):
    make("Quentin", ["Austin"], [D1], "500", ["Hiking"])
    make("Rosalind", ["Miami"], [D2], "900", ["Beach"])
    html = client.get(reverse("summary")).content.decode()
    assert "Quentin" not in html and "Rosalind" not in html


@pytest.mark.django_db
def test_summary_page_with_no_submissions(client):
    r = client.get(reverse("summary"))
    assert r.status_code == 200
    assert "No submissions yet" in r.content.decode()


@pytest.mark.django_db
def test_summary_page_updates_when_a_member_edits(client):
    member = make("Quentin", ["Austin"])
    assert "Austin" in client.get(reverse("summary")).content.decode()
    member.remove_destination("Austin")
    member.add_destination("Portland")
    html = client.get(reverse("summary")).content.decode()
    assert "Portland" in html and "Austin" not in html
