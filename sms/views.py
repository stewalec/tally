import logging
import json

import plivo
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from games.models import BracketCityScore, ConnectionsScore, WordleScore, Game, Score
from games.parsers import PARSERS
from games.parsers.base import ParseError
from users.models import TallyUser, normalize_phone

logger = logging.getLogger(__name__)


def _send_sms(to: str, message: str):
    """Send an outbound SMS via Plivo."""
    try:
        client = plivo.RestClient(settings.PLIVO_AUTH_ID, settings.PLIVO_AUTH_TOKEN)
        client.messages.create(
            src=settings.PLIVO_PHONE_NUMBER,
            dst=to,
            text=message,
        )
    except Exception as exc:
        logger.error("Failed to send SMS to %s: %s", to, exc)


@csrf_exempt
@require_POST
def sms_webhook(request):
    """Plivo inbound SMS webhook."""
    data = json.loads(request.body)
    from_number = data.get("From").strip()
    text = data.get("Text", "").strip()

    if not from_number or not text:
        return HttpResponse(status=200)

    normalized = normalize_phone(from_number)
    if not normalized:
        logger.warning("Could not normalize inbound number: %s", from_number)
        return HttpResponse(status=200)

    # Look up the user
    try:
        user = TallyUser.objects.get(phone_number=normalized, is_active=True)
    except TallyUser.DoesNotExist:
        _send_sms(
            from_number,
            "Your number is not registered with Tally. Contact an admin to get access.",
        )
        return HttpResponse(status=200)

    from django.utils import timezone
    submitted_at = timezone.now()

    # Find a matching parser
    matched_parser = None
    for parser in PARSERS:
        if parser.can_parse(text):
            matched_parser = parser
            break

    if matched_parser is None:
        _send_sms(
            user.phone_number,
            "Couldn't recognize this score. Make sure you're sending the share text directly from Bracket City, NYT Connections, or Wordle.",
        )
        return HttpResponse(status=200)

    # Parse the score
    try:
        parsed = matched_parser.parse(text, submitted_at)
    except ParseError as exc:
        _send_sms(
            user.phone_number,
            f"Couldn't parse your score: {exc}\n\nMake sure you send the full share text from the game.",
        )
        return HttpResponse(status=200)

    # Look up the game
    try:
        game = Game.objects.get(slug=parsed.game_slug, is_active=True)
    except Game.DoesNotExist:
        logger.error("Game not found for slug: %s", parsed.game_slug)
        _send_sms(user.phone_number, "Game not found in Tally. Contact an admin.")
        return HttpResponse(status=200)

    # Duplicate check
    if Score.objects.filter(user=user, game=game, game_identifier=parsed.game_identifier).exists():
        _send_sms(
            user.phone_number,
            f"You already submitted your {game.name} score for this puzzle!",
        )
        return HttpResponse(status=200)

    # Save the score
    try:
        with transaction.atomic():
            score = Score.objects.create(
                user=user,
                game=game,
                raw_text=text,
                calculated_score=parsed.calculated_score,
                puzzle_date=parsed.puzzle_date,
                game_identifier=parsed.game_identifier,
            )

            if parsed.game_slug == "bracket-city":
                d = parsed.raw_details
                BracketCityScore.objects.create(
                    score=score,
                    total_score=d["total_score"],
                    rank=d["rank"],
                    rank_emoji=d["rank_emoji"],
                    wrong_guesses=d["wrong_guesses"],
                    peeks=d["peeks"],
                    difficulty=d["difficulty"],
                )
            elif parsed.game_slug == "connections":
                d = parsed.raw_details
                ConnectionsScore.objects.create(
                    score=score,
                    puzzle_number=d["puzzle_number"],
                    attempts_grid=d["grid"],
                    wrong_guesses=d["wrong_guesses"],
                    solved=d["solved"],
                    first_solved_category=d["first_solved_category"],
                    correct_categories=d["correct_categories"],
                )
            elif parsed.game_slug == "wordle":
                d = parsed.raw_details
                WordleScore.objects.create(
                    score=score,
                    puzzle_number=d["puzzle_number"],
                    attempts_grid=d["grid"],
                    attempts=d["attempts"],
                    solved=d["solved"],
                )
    except Exception as exc:
        logger.exception("Error saving score for %s: %s", user, exc)
        _send_sms(user.phone_number, "Something went wrong saving your score. Please try again.")
        return HttpResponse(status=200)

    score_str = f"{parsed.calculated_score:.1f}"
    _send_sms(
        user.phone_number,
        f"Score received for {game.name}!\nScore: {score_str}",
    )
    return HttpResponse(status=200)
