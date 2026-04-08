import re
from datetime import datetime
from zoneinfo import ZoneInfo

from .base import BaseParser, ParsedScore, ParseError

ET = ZoneInfo("America/New_York")

# Maps the difficulty text that appears inside parentheses on the date line.
VALID_DIFFICULTIES = {"Easy", "Medium", "Hard"}


class BracketCityParser(BaseParser):
    def can_parse(self, text: str) -> bool:
        return "[Bracket City]" in text

    def parse(self, text: str, submitted_at) -> ParsedScore:
        lines = [l.strip() for l in text.strip().splitlines()]
        # Remove blank lines for easier scanning
        non_empty = [l for l in lines if l]

        if not any("[Bracket City]" in l for l in non_empty):
            raise ParseError("Not a Bracket City score")

        # --- Date & difficulty ---
        puzzle_date = None
        difficulty = "Unknown"
        for line in non_empty:
            date_match = re.search(
                r"(January|February|March|April|May|June|July|August|September|October|November|December)"
                r"\s+\d{1,2},\s+\d{4}",
                line,
            )
            if date_match:
                try:
                    puzzle_date = datetime.strptime(date_match.group(0), "%B %d, %Y").date()
                except ValueError:
                    raise ParseError(f"Could not parse date: {date_match.group(0)!r}")
                diff_match = re.search(r"\((\w+)\)", line)
                if diff_match and diff_match.group(1) in VALID_DIFFICULTIES:
                    difficulty = diff_match.group(1)
                break

        if puzzle_date is None:
            raise ParseError("Could not find puzzle date in Bracket City score")

        # --- Rank ---
        rank = ""
        rank_emoji = ""
        for line in non_empty:
            if line.startswith("Rank:"):
                # e.g. "Rank: 💼 (Power Broker)"
                rank_match = re.search(r"Rank:\s*(.+?)\s*\((.+?)\)", line)
                if rank_match:
                    rank_emoji = rank_match.group(1).strip()
                    rank = rank_match.group(2).strip()
                break

        # --- Wrong guesses ---
        wrong_guesses = 0
        for line in non_empty:
            wg_match = re.search(r"Wrong guesses:\s*(\d+)", line)
            if wg_match:
                wrong_guesses = int(wg_match.group(1))
                break

        # --- Peeks ---
        peeks = 0
        for line in non_empty:
            p_match = re.search(r"Peeks:\s*(\d+)", line)
            if p_match:
                peeks = int(p_match.group(1))
                break

        # --- Total Score ---
        total_score = None
        for line in non_empty:
            ts_match = re.search(r"Total Score:\s*(\d+(?:\.\d+)?)", line)
            if ts_match:
                total_score = float(ts_match.group(1))
                break

        if total_score is None:
            raise ParseError("Could not find Total Score in Bracket City score")

        return ParsedScore(
            game_slug="bracket-city",
            game_identifier=puzzle_date.strftime("%Y-%m-%d"),
            puzzle_date=puzzle_date,
            calculated_score=total_score,
            raw_details={
                "total_score": total_score,
                "rank": rank,
                "rank_emoji": rank_emoji,
                "wrong_guesses": wrong_guesses,
                "peeks": peeks,
                "difficulty": difficulty,
            },
        )
