"""
Group summary: combines every member's submitted preferences into one
anonymous overview. Nothing here returns names or ties an answer to a person.
"""
import datetime as dt
from collections import Counter
from decimal import Decimal
from statistics import median

# A budget counts as an outlier when it is this far from the group's median.
OUTLIER_RATIO = Decimal("0.5")  # 50% below or above
# Outliers are only flagged in groups this big, so they can't point at one person.
MIN_GROUP_FOR_OUTLIERS = 3
# Longest single date range counted, in days, so one bad entry can't slow the page.
MAX_RANGE_DAYS = 366


def _tally(lists):
    """
    Count how many members mention each item.

    Matching ignores case and extra spaces, so "denver " and "Denver" are one
    entry. Each member counts at most once per item. The label shown is the
    first spelling seen.
    """
    counts = Counter()
    labels = {}
    for items in lists:
        seen = set()
        for raw in items or []:
            text = " ".join(str(raw).split())
            key = text.casefold()
            if not key or key in seen:
                continue
            seen.add(key)
            labels.setdefault(key, text)
            counts[key] += 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], labels[kv[0]].casefold()))
    return [{"name": labels[key], "count": n} for key, n in ranked]


def _member_days(member):
    """
    Every day a member is free, from their date ranges (start and end included).
    Ranges with the end before the start are skipped, and very long ranges are
    capped so one bad entry can't make the page slow.
    """
    days = set()
    for r in member.available_ranges.all():
        start, end = r.startDate, r.endDate
        if not start or not end or end < start:
            continue
        end = min(end, start + dt.timedelta(days=MAX_RANGE_DAYS - 1))
        days.update(start + dt.timedelta(days=i) for i in range((end - start).days + 1))
    return days


def _runs(days):
    """Group sorted days into consecutive runs: [(start, end), ...]."""
    runs = []
    for day in days:
        if runs and day - runs[-1][1] == dt.timedelta(days=1):
            runs[-1][1] = day
        else:
            runs.append([day, day])
    return [{"start": a, "end": b, "days": (b - a).days + 1} for a, b in runs]


def _availability(members):
    day_sets = [_member_days(m) for m in members]
    day_sets = [d for d in day_sets if d]
    if not day_sets:
        return {"responded": 0, "common": [], "common_ranges": [], "best": []}

    common = sorted(set.intersection(*day_sets))
    counts = Counter(day for days in day_sets for day in days)
    best = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    return {
        "responded": len(day_sets),
        "common": common,
        "common_ranges": _runs(common),
        "best": [{"date": d, "count": n} for d, n in best],
    }


def _budget(members):
    budgets = sorted(m.budget for m in members if m.budget is not None)
    if not budgets:
        return {"responded": 0}

    mid = Decimal(median(budgets))
    summary = {
        "responded": len(budgets),
        "min": budgets[0],
        "max": budgets[-1],
        "average": (sum(budgets) / len(budgets)).quantize(Decimal("0.01")),
        "median": mid.quantize(Decimal("0.01")),
        "below": 0,
        "above": 0,
        "outliers_checked": len(budgets) >= MIN_GROUP_FOR_OUTLIERS,
    }
    if summary["outliers_checked"] and mid > 0:
        summary["below"] = sum(1 for b in budgets if b < mid * (1 - OUTLIER_RATIO))
        summary["above"] = sum(1 for b in budgets if b > mid * (1 + OUTLIER_RATIO))
    return summary


def build_group_summary(members):
    """
    Summarize a collection of core.User objects. Never includes names.
    Pass a queryset with prefetch_related("available_ranges") to avoid one
    database query per member.
    """
    members = list(members)
    return {
        "member_count": len(members),
        "destinations": _tally(m.destinations for m in members),
        "activities": _tally(m.activities for m in members),
        "availability": _availability(members),
        "budget": _budget(members),
    }
