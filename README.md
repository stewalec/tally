# Tally

Score tracking web app for daily word games. Players submit scores via SMS to a [Plivo](https://www.plivo.com/) phone number; the app parses each message, calculates a normalized score, and displays leaderboards and per-player stats.

Currently supported games: **Bracket City** and **NYT Connections**.

## How it works

1. A player texts their game results to the Tally phone number.
2. The SMS webhook parses the message and stores the score.
3. The player gets a confirmation reply with their score.
4. Leaderboards and stats update in real time on the web UI.

## Tech stack

- **Django** with SQLite
- **Plivo** for inbound/outbound SMS
- **uv** for Python package management
- Phone-based OTP authentication (no passwords)
- Vanilla HTML/CSS/JS frontend with light/dark theme support

## Setup

```bash
# Install dependencies
uv sync

# Configure environment
cp .env.example .env  # then fill in Plivo credentials and Django secret key

# Seed games and create superuser
uv run python setup.py

# Run the dev server
uv run python manage.py runserver
```

Users are added via the Django admin (`/admin/`) — there is no public registration.

## Adding a new game

1. Create a parser in `games/parsers/` extending `BaseParser`
2. Register it in `games/parsers/__init__.py`
3. Add a `Game` row via Django admin (slug must match the parser's `game_slug`)

---

This project was built with the help of ([Claude Code](https://claude.ai/code)).
