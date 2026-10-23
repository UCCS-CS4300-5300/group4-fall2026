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


def _parse_dates(values):
    """Turn a member's available dates into a set of dates, skipping bad entries."""
    dates = set()
    for value in values or []:
        if isinstance(value, dt.date):
            dates.add(value)
            continue
        try:
            dates.add(dt.date.fromisoformat(str(value).strip()))
        except ValueError:
            continue
    return dates


def _availability(members):
    date_sets = [_parse_dates(m.availableDates) for m in members]
    date_sets = [s for s in date_sets if s]
    if not date_sets:
        return {"responded": 0, "common": [], "best": []}

    common = sorted(set.intersection(*date_sets))
    counts = Counter(d for s in date_sets for d in s)
    best = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    return {
        "responded": len(date_sets),
        "common": common,
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
    """Summarize a collection of core.User objects. Never includes names."""
    members = list(members)
    return {
        "member_count": len(members),
        "destinations": _tally(m.destinations for m in members),
        "activities": _tally(m.activities for m in members),
        "availability": _availability(members),
        "budget": _budget(members),
    }
