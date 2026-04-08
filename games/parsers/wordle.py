import re
from zoneinfo import ZoneInfo

from .base import BaseParser, ParsedScore, ParseError

ET = ZoneInfo("America/New_York")

GREEN  = "\U0001f7e9"   # 🟩
YELLOW = "\U0001f7e8"   # 🟨
BLACK  = "\u2b1b"       # ⬛
WHITE  = "\u2b1c"       # ⬜

KNOWN_SQUARES = {GREEN, YELLOW, BLACK, WHITE}

SQUARE_NAMES = {
    GREEN:  "green",
    YELLOW: "yellow",
    BLACK:  "absent",
    WHITE:  "absent",
}

# Points awarded by attempt number (fewer attempts = more points).
SCORE_BY_ATTEMPT = {
    1: 100,
    2: 85,
    3: 70,
    4: 55,
    5: 40,
    6: 25,
}


class WordleParser(BaseParser):
    def can_parse(self, text: str) -> bool:
        first_line = text.strip().splitlines()[0].strip() if text.strip() else ""
        return bool(re.match(r"Wordle\s[\d,]+\s", first_line))

    def parse(self, text: str, submitted_at) -> ParsedScore:
        lines = [l.strip() for l in text.strip().splitlines() if l.strip()]

        if not lines:
            raise ParseError("Empty Wordle score")

        # --- Header: "Wordle 1,720 2/6" or "Wordle 1,720 X/6" ---
        header_match = re.match(
            r"Wordle\s+([\d,]+)\s+([X1-6])/6",
            lines[0],
        )
        if not header_match:
            raise ParseError("Could not parse Wordle header")

        puzzle_number = int(header_match.group(1).replace(",", ""))
        attempts_raw = header_match.group(2)
        solved = attempts_raw != "X"
        attempts = int(attempts_raw) if solved else 6

        # --- Grid ---
        grid: list[list[str]] = []
        for line in lines[1:]:
            row = [ch for ch in line if ch in KNOWN_SQUARES]
            if not row:
                continue
            if len(row) != 5:
                raise ParseError(f"Expected 5 squares per row, got {len(row)}: {line!r}")
            grid.append(row)

        if not grid:
            raise ParseError("No emoji grid found in Wordle score")

        expected_rows = attempts
        if len(grid) != expected_rows:
            raise ParseError(
                f"Header says {attempts_raw}/6 but found {len(grid)} grid rows"
            )

        # --- Score ---
        calculated_score = SCORE_BY_ATTEMPT.get(attempts, 0) if solved else 0

        puzzle_date = submitted_at.astimezone(ET).date()

        return ParsedScore(
            game_slug="wordle",
            game_identifier=str(puzzle_number),
            puzzle_date=puzzle_date,
            calculated_score=calculated_score,
            raw_details={
                "puzzle_number": puzzle_number,
                "grid": [[SQUARE_NAMES[sq] for sq in row] for row in grid],
                "attempts": attempts,
                "solved": solved,
            },
        )
