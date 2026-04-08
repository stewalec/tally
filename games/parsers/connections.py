import re
from zoneinfo import ZoneInfo

from .base import BaseParser, ParsedScore, ParseError

ET = ZoneInfo("America/New_York")

YELLOW = "\U0001f7e8"   # 🟨
GREEN  = "\U0001f7e9"   # 🟩
BLUE   = "\U0001f7e6"   # 🟦
PURPLE = "\U0001f7ea"   # 🟪

KNOWN_COLORS = {YELLOW, GREEN, BLUE, PURPLE}

COLOR_NAMES = {
    YELLOW: "Yellow",
    GREEN:  "Green",
    BLUE:   "Blue",
    PURPLE: "Purple",
}

# Bonus points for solving a category first (hardest category first = bigger reward)
FIRST_SOLVE_BONUS = {
    "Yellow": 0,
    "Green":  5,
    "Blue":   10,
    "Purple": 15,
}


class ConnectionsParser(BaseParser):
    def can_parse(self, text: str) -> bool:
        lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
        return (
            len(lines) >= 3
            and lines[0] == "Connections"
            and lines[1].startswith("Puzzle #")
        )

    def parse(self, text: str, submitted_at) -> ParsedScore:
        lines = [l.strip() for l in text.strip().splitlines() if l.strip()]

        if not lines or lines[0] != "Connections":
            raise ParseError("Not a Connections score")

        if len(lines) < 3:
            raise ParseError("Connections score is too short")

        # --- Puzzle number ---
        puzzle_match = re.match(r"Puzzle #(\d+)", lines[1])
        if not puzzle_match:
            raise ParseError("Could not parse Connections puzzle number")
        puzzle_number = int(puzzle_match.group(1))

        # --- Grid ---
        grid: list[list[str]] = []
        for line in lines[2:]:
            # Extract only the four known color emoji from the line
            row = [ch for ch in line if ch in KNOWN_COLORS]
            if not row:
                continue
            if len(row) != 4:
                raise ParseError(f"Expected 4 squares per row, got {len(row)}: {line!r}")
            grid.append(row)

        if not grid:
            raise ParseError("No emoji grid found in Connections score")

        # --- Analyse grid ---
        correct_categories: list[str] = []
        wrong_guesses = 0

        for row in grid:
            if len(set(row)) == 1:
                # All four squares the same colour → correct guess
                correct_categories.append(COLOR_NAMES[row[0]])
            else:
                wrong_guesses += 1

        solved = len(correct_categories) == 4
        first_solved = correct_categories[0] if correct_categories else None

        # --- Score ---
        bonus = FIRST_SOLVE_BONUS.get(first_solved, 0) if first_solved else 0
        calculated_score = max(0.0, 100.0 - wrong_guesses * 10 + bonus) if solved else 0

        # puzzle_date is derived from the submission timestamp in ET
        puzzle_date = submitted_at.astimezone(ET).date()

        return ParsedScore(
            game_slug="connections",
            game_identifier=str(puzzle_number),
            puzzle_date=puzzle_date,
            calculated_score=calculated_score,
            raw_details={
                "puzzle_number": puzzle_number,
                "grid": [[COLOR_NAMES[c] for c in row] for row in grid],
                "wrong_guesses": wrong_guesses,
                "solved": solved,
                "first_solved_category": first_solved or "",
                "correct_categories": correct_categories,
            },
        )
