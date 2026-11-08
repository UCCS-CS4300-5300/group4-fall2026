"""Group summary (Joseph): combining everyone's preferences, and the summary page."""
import datetime as dt
from decimal import Decimal

import pytest
from django.urls import reverse

from core.models import Trip, User
from core.summary import build_group_summary


def day(n):
    """December n, 2026."""
    return dt.date(2026, 12, n)


def make(name, destinations=(), ranges=(), budget=None, activities=(), trip=None):
    """
    Create a member. ranges is a list of (start, end) dates, both included.
    Pass trip to add the member to that trip.
    """
    user = User.objects.create(
        name=name,
        destinations=list(destinations),
        budget=None if budget is None else Decimal(budget),
        activities=list(activities),
    )
    for start, end in ranges:
        user.add_available_date_range(start, end)
    if trip is not None:
        trip.add_user(user)
    return user


def summarize():
    return build_group_summary(User.objects.prefetch_related("available_ranges"))


# ---- Combining preferences --------------------------------------------------

@pytest.mark.django_db
def test_no_members_gives_empty_summary():
    s = summarize()
    assert s["member_count"] == 0
    assert s["destinations"] == [] and s["activities"] == []
    assert s["availability"]["responded"] == 0
    assert s["budget"]["responded"] == 0


@pytest.mark.django_db
def test_destinations_ranked_by_how_many_members_suggest_them():
    make("Quentin", ["Denver", "Austin"])
    make("Rosalind", ["Austin", "Chicago"])
    make("Thaddeus", ["Austin", "Denver"])
    s = summarize()
    assert s["destinations"] == [
        {"name": "Austin", "count": 3},
        {"name": "Denver", "count": 2},
        {"name": "Chicago", "count": 1},
    ]


@pytest.mark.django_db
def test_matching_ignores_case_and_spacing_and_counts_each_member_once():
    make("Quentin", ["Denver", "  denver "], activities=["Live Music"])
    make("Rosalind", ["DENVER"], activities=["live  music"])
    s = summarize()
    assert s["destinations"] == [{"name": "Denver", "count": 2}]
    assert s["activities"] == [{"name": "Live Music", "count": 2}]


@pytest.mark.django_db
def test_common_dates_are_where_everyones_ranges_overlap():
    make("Quentin", ranges=[(day(15), day(22))])
    make("Rosalind", ranges=[(day(18), day(25))])
    make("Thaddeus", ranges=[(day(10), day(20))])
    a = summarize()["availability"]
    assert a["responded"] == 3
    assert a["common"] == [day(18), day(19), day(20)]
    assert a["common_ranges"] == [{"start": day(18), "end": day(20), "days": 3}]


@pytest.mark.django_db
def test_a_member_with_several_ranges_counts_all_of_them():
    make("Quentin", ranges=[(day(1), day(3)), (day(20), day(22))])
    make("Rosalind", ranges=[(day(2), day(21))])
    a = summarize()["availability"]
    assert a["common_ranges"] == [
        {"start": day(2), "end": day(3), "days": 2},
        {"start": day(20), "end": day(21), "days": 2},
    ]


@pytest.mark.django_db
def test_without_a_common_date_the_best_dates_are_listed():
    make("Quentin", ranges=[(day(18), day(19))])
    make("Rosalind", ranges=[(day(19), day(19))])
    make("Thaddeus", ranges=[(day(25), day(26))])
    a = summarize()["availability"]
    assert a["common"] == []
    assert a["best"][0] == {"date": day(19), "count": 2}


@pytest.mark.django_db
def test_members_without_dates_and_backwards_ranges_are_ignored():
    make("Quentin", ranges=[(day(18), day(20))])
    rosalind = make("Rosalind", ranges=[(day(19), day(21))])
    # A backwards range can't come from add_available_date_range, but can from the admin.
    rosalind.available_ranges.create(startDate=day(30), endDate=day(5))
    make("Thaddeus")  # no dates yet; shouldn't wipe out the overlap
    a = summarize()["availability"]
    assert a["responded"] == 2
    assert a["common"] == [day(19), day(20)]


@pytest.mark.django_db
def test_very_long_ranges_are_capped():
    make("Quentin", ranges=[(dt.date(2026, 1, 1), dt.date(2030, 12, 31))])
    a = summarize()["availability"]
    assert len(a["common"]) == 366


@pytest.mark.django_db
def test_budget_range_average_and_median():
    for name, budget in [("Quentin", "400"), ("Rosalind", "600"), ("Thaddeus", "800"), ("Ulrich", None)]:
        make(name, budget=budget)
    b = summarize()["budget"]
    assert b["responded"] == 3
    assert (b["min"], b["max"]) == (Decimal("400"), Decimal("800"))
    assert b["average"] == Decimal("600.00")
    assert b["median"] == Decimal("600.00")
    assert b["below"] == b["above"] == 0


@pytest.mark.django_db
def test_budget_outliers_are_counted_not_named():
    for name, budget in [("Quentin", "150"), ("Rosalind", "600"), ("Thaddeus", "650"), ("Ulrich", "2000")]:
        make(name, budget=budget)
    b = summarize()["budget"]
    assert (b["below"], b["above"]) == (1, 1)


@pytest.mark.django_db
def test_outliers_not_flagged_in_tiny_groups():
    """With two people, 'one budget is far lower' would reveal who it is."""
    make("Quentin", budget="100")
    make("Rosalind", budget="2000")
    b = summarize()["budget"]
    assert b["outliers_checked"] is False
    assert b["below"] == b["above"] == 0


# ---- The page ---------------------------------------------------------------

def activate(client, trip):
    """Make trip the active trip in client's session, as login does."""
    session = client.session
    session["active_trip_id"] = trip.pk
    session.save()


@pytest.fixture
def trip(client):
    """A trip that is already the active trip for the test client."""
    trip = Trip.objects.create(name="Winter break")
    activate(client, trip)
    return trip


def page(client):
    return client.get(reverse("core:summary")).content.decode()


@pytest.mark.django_db
def test_summary_page_shows_combined_preferences(client, trip):
    make("Quentin", ["Austin"], [(day(17), day(22))], "500", ["Hiking"], trip=trip)
    make("Rosalind", ["Austin", "Miami"], [(day(18), day(20))], "700", ["Beach"], trip=trip)
    make("Thaddeus", ["Austin"], [(day(19), day(19))], "650", ["Hiking"], trip=trip)
    r = client.get(reverse("core:summary"))
    html = r.content.decode()
    assert r.status_code == 200
    assert "Winter break" in html
    assert "3 members have submitted" in html
    for text in ["Austin", "Miami", "Hiking", "Beach", "Sat, Dec 19, 2026", "$500 – $700"]:
        assert text in html, text


@pytest.mark.django_db
def test_summary_page_only_counts_the_active_trips_members(client, trip):
    make("Quentin", ["Austin"], budget="500", trip=trip)
    other = Trip.objects.create(name="Spring break")
    make("Rosalind", ["Miami"], budget="9000", trip=other)
    make("Thaddeus", ["Chicago"])  # in no trip at all
    html = page(client)
    assert "1 member has submitted" in html
    assert "Austin" in html
    assert "Miami" not in html and "Chicago" not in html and "9000" not in html


@pytest.mark.django_db
def test_switching_active_trip_switches_the_summary(client, trip):
    make("Quentin", ["Austin"], trip=trip)
    other = Trip.objects.create(name="Spring break")
    make("Rosalind", ["Miami"], trip=other)
    activate(client, other)
    html = page(client)
    assert "Spring break" in html and "Miami" in html and "Austin" not in html


@pytest.mark.django_db
def test_summary_page_never_shows_names(client, trip):
    make("Quentin", ["Austin"], [(day(18), day(20))], "500", ["Hiking"], trip=trip)
    make("Rosalind", ["Miami"], [(day(19), day(22))], "900", ["Beach"], trip=trip)
    html = page(client)
    assert "Quentin" not in html and "Rosalind" not in html


@pytest.mark.django_db
def test_common_range_shown_as_a_span(client, trip):
    make("Quentin", ranges=[(day(18), day(22))], trip=trip)
    make("Rosalind", ranges=[(day(19), day(21))], trip=trip)
    assert "Dec 19 – Dec 21, 2026 (3 days)" in page(client)


@pytest.mark.django_db
def test_summary_page_query_count_does_not_grow_with_members(client, trip, django_assert_max_num_queries):
    for i in range(10):
        make(f"Member{i}", ["Austin"], [(day(18), day(20))], "500", trip=trip)
    # session, trip, members, date ranges
    with django_assert_max_num_queries(4):
        client.get(reverse("core:summary"))


@pytest.mark.django_db
def test_trip_with_no_members_shows_empty_state(client, trip):
    r = client.get(reverse("core:summary"))
    html = r.content.decode()
    assert r.status_code == 200
    assert "No submissions yet" in html
    assert "See AI suggestions" not in html


@pytest.mark.django_db
def test_without_an_active_trip_the_page_asks_to_start_or_join_one(client):
    make("Quentin", ["Austin"])  # data exists, but no trip is active
    r = client.get(reverse("core:summary"))
    html = r.content.decode()
    assert r.status_code == 200
    assert "No trip selected" in html
    assert f'href="{reverse("core:home")}"' in html
    assert "Austin" not in html


@pytest.mark.django_db
def test_a_deleted_active_trip_is_treated_as_no_trip(client, trip):
    make("Quentin", ["Austin"], trip=trip)
    trip.delete()
    html = page(client)
    assert "No trip selected" in html and "Austin" not in html


@pytest.mark.django_db
def test_summary_page_links_to_ai_suggestions(client, trip):
    make("Quentin", ["Austin"], trip=trip)
    html = page(client)
    assert "See AI suggestions" in html
    assert f'href="{reverse("core:ai_output")}"' in html


@pytest.mark.django_db
def test_summary_page_updates_when_a_member_edits(client, trip):
    member = make("Quentin", ["Austin"], trip=trip)
    assert "Austin" in page(client)
    member.remove_destination("Austin")
    member.add_destination("Portland")
    html = page(client)
    assert "Portland" in html and "Austin" not in html