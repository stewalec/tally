"""
Stats calculations for individual users and leaderboard aggregations.
All "today" logic is relative to US Eastern time.
"""
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from django.db.models import Avg, Count, Max, Min, QuerySet

ET = ZoneInfo("America/New_York")


def today_et() -> date:
    from django.utils import timezone
    return timezone.now().astimezone(ET).date()


# ---------------------------------------------------------------------------
# Streak helpers
# ---------------------------------------------------------------------------

def _current_streak(dates: list[date]) -> int:
    """
    Given a sorted (ascending) list of unique puzzle dates, return the current streak.
    A streak is still active if the most recent play was today or yesterday.
    """
    if not dates:
        return 0

    unique = sorted(set(dates), reverse=True)
    today = today_et()
    yesterday = today - timedelta(days=1)

    # Streak broken if user hasn't played today or yesterday
    if unique[0] < yesterday:
        return 0

    streak = 0
    expected = unique[0]
    for d in unique:
        if d == expected:
            streak += 1
            expected -= timedelta(days=1)
        else:
            break
    return streak


def _longest_streak(dates: list[date]) -> int:
    """Return the all-time longest streak from a sorted date list."""
    if not dates:
        return 0

    unique = sorted(set(dates))
    best = 1
    current = 1

    for i in range(1, len(unique)):
        if unique[i] - unique[i - 1] == timedelta(days=1):
            current += 1
            best = max(best, current)
        else:
            current = 1

    return best


# ---------------------------------------------------------------------------
# Per-user, per-game stats
# ---------------------------------------------------------------------------

def user_game_stats(user, game) -> dict:
    """Return a stats dict for one user + one game across all time."""
    from games.models import Score

    qs = Score.objects.filter(user=user, game=game).order_by("puzzle_date")
    dates = list(qs.values_list("puzzle_date", flat=True))
    scores = list(qs.values_list("calculated_score", flat=True))

    if not scores:
        return {
            "total_games": 0,
            "avg_score": None,
            "best_score": None,
            "worst_score": None,
            "current_streak": 0,
            "longest_streak": 0,
            "today_score": None,
        }

    today = today_et()
    today_score_obj = qs.filter(puzzle_date=today).first()

    return {
        "total_games": len(scores),
        "avg_score": round(sum(scores) / len(scores), 1),
        "best_score": max(scores),
        "worst_score": min(scores),
        "current_streak": _current_streak(dates),
        "longest_streak": _longest_streak(dates),
        "today_score": today_score_obj,
    }


def user_game_stats_period(user, game, start_date: date | None, end_date: date | None) -> dict:
    """Return aggregated stats for a user + game within an optional date range."""
    from games.models import Score

    qs = Score.objects.filter(user=user, game=game)
    if start_date:
        qs = qs.filter(puzzle_date__gte=start_date)
    if end_date:
        qs = qs.filter(puzzle_date__lte=end_date)

    agg = qs.aggregate(
        avg=Avg("calculated_score"),
        best=Max("calculated_score"),
        worst=Min("calculated_score"),
        count=Count("id"),
    )
    return {
        "total_games": agg["count"] or 0,
        "avg_score": round(agg["avg"], 1) if agg["avg"] is not None else None,
        "best_score": agg["best"],
        "worst_score": agg["worst"],
    }


# ---------------------------------------------------------------------------
# Leaderboard builder
# ---------------------------------------------------------------------------

def build_leaderboard(game, period: str) -> list[dict]:
    """
    Return a list of dicts (one per active user) sorted best→worst
    for the given game and time period.

    period: 'today' | 'week' | 'month' | 'all'
    """
    from games.models import Score
    from users.models import TallyUser

    today = today_et()
    start_date, end_date = _period_bounds(period, today)

    users = TallyUser.objects.filter(is_active=True)
    rows = []

    for user in users:
        all_dates = list(
            Score.objects.filter(user=user, game=game)
            .values_list("puzzle_date", flat=True)
        )

        period_qs = Score.objects.filter(user=user, game=game)
        if start_date:
            period_qs = period_qs.filter(puzzle_date__gte=start_date)
        if end_date:
            period_qs = period_qs.filter(puzzle_date__lte=end_date)

        period_count = period_qs.count()

        if period == "today":
            today_score = period_qs.filter(puzzle_date=today).first()
            display_score = today_score.calculated_score if today_score else None
            score_obj = today_score
        else:
            agg = period_qs.aggregate(avg=Avg("calculated_score"))
            display_score = round(agg["avg"], 1) if agg["avg"] is not None else None
            score_obj = None

        rows.append(
            {
                "user": user,
                "display_score": display_score,
                "score_obj": score_obj,
                "period_games": period_count,
                "current_streak": _current_streak(all_dates),
                "all_time_games": len(all_dates),
            }
        )

    # Sort: submitted scores first (highest first), then non-submitters
    rows.sort(key=lambda r: (r["display_score"] is None, -(r["display_score"] or 0)))
    for i, row in enumerate(rows):
        row["rank"] = i + 1 if row["display_score"] is not None else None

    return rows


def _period_bounds(period: str, today: date) -> tuple[date | None, date | None]:
    if period == "today":
        return today, today
    if period == "week":
        # Monday → today
        monday = today - timedelta(days=today.weekday())
        return monday, today
    if period == "month":
        return today.replace(day=1), today
    # all
    return None, None
