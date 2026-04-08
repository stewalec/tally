from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import Game, Score, BracketCityScore, ConnectionsScore
from .stats import build_leaderboard, user_game_stats, today_et


@login_required
def leaderboard(request):
    games = Game.objects.filter(is_active=True)
    if not games.exists():
        return render(request, "leaderboard/index.html", {"games": [], "rows": [], "current_game": None})

    game_slug = request.GET.get("game", games.first().slug)
    period = request.GET.get("period", "today")
    if period not in ("today", "week", "month", "all"):
        period = "today"

    current_game = get_object_or_404(Game, slug=game_slug, is_active=True)
    rows = build_leaderboard(current_game, period)

    period_choices = [
        ("Today", "today"),
        ("This Week", "week"),
        ("This Month", "month"),
        ("All Time", "all"),
    ]

    from django.conf import settings

    return render(
        request,
        "leaderboard/index.html",
        {
            "games": games,
            "current_game": current_game,
            "period": period,
            "period_choices": period_choices,
            "rows": rows,
            "today": today_et(),
            "plivo_number": settings.PLIVO_PHONE_NUMBER,
        },
    )


@login_required
def user_detail(request, username):
    from users.models import TallyUser

    target_user = get_object_or_404(TallyUser, username=username, is_active=True)
    games = Game.objects.filter(is_active=True)

    game_slug = request.GET.get("game", games.first().slug if games.exists() else None)
    current_game = get_object_or_404(Game, slug=game_slug, is_active=True) if game_slug else None

    stats = {}
    score_history = []

    if current_game:
        stats = user_game_stats(target_user, current_game)

        # Score history — optionally filtered by date range from query params
        qs = Score.objects.filter(user=target_user, game=current_game).order_by("-puzzle_date")

        date_from = request.GET.get("from")
        date_to = request.GET.get("to")
        if date_from:
            try:
                qs = qs.filter(puzzle_date__gte=date.fromisoformat(date_from))
            except ValueError:
                pass
        if date_to:
            try:
                qs = qs.filter(puzzle_date__lte=date.fromisoformat(date_to))
            except ValueError:
                pass

        score_history = list(qs.select_related("bracket_city_detail", "connections_detail"))

    return render(
        request,
        "users/detail.html",
        {
            "target_user": target_user,
            "games": games,
            "current_game": current_game,
            "stats": stats,
            "score_history": score_history,
            "date_from": request.GET.get("from", ""),
            "date_to": request.GET.get("to", ""),
        },
    )
