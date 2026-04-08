from dataclasses import dataclass, field
from datetime import date


class ParseError(Exception):
    """Raised when a score text cannot be parsed."""


@dataclass
class ParsedScore:
    game_slug: str           # matches Game.slug in the database
    game_identifier: str     # stable unique key for this puzzle
    puzzle_date: date        # ET date of the puzzle
    calculated_score: float  # primary numeric score used for rankings
    raw_details: dict = field(default_factory=dict)  # game-specific extra data


class BaseParser:
    """Interface every game parser must implement."""

    def can_parse(self, text: str) -> bool:
        raise NotImplementedError

    def parse(self, text: str, submitted_at) -> ParsedScore:
        """Parse *text* into a ParsedScore.  submitted_at is a timezone-aware datetime."""
        raise NotImplementedError
