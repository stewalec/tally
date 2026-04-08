"""
Run this once after `migrate` to seed the database with the two default games
and create a superuser for the Django admin.

    uv run python setup.py
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tally.settings")
django.setup()

from games.models import Game
from users.models import TallyUser

# ── Seed games ────────────────────────────────────────────────────────────────
games = [
    {"name": "Bracket City", "slug": "bracket-city", "order": 1,
     "description": "Daily bracket puzzle from The Atlantic."},
    {"name": "NYT Connections", "slug": "connections", "order": 2,
     "description": "Group the 16 words into four categories."},
    {"name": "Wordle", "slug": "wordle", "order": 3,
     "description": "Guess the five-letter word in six tries."},
]

for g in games:
    obj, created = Game.objects.get_or_create(slug=g["slug"], defaults=g)
    if created:
        print(f"Created game: {obj.name}")
    else:
        print(f"Game already exists: {obj.name}")

# ── Superuser ──────────────────────────────────────────────────────────────────
print("\nCreate a Django admin superuser")
phone = input("Phone number (E.164 or US format): ").strip()
password = input("Password: ").strip()
first_name = input("First Name: ").strip()
last_name = input("Last Name: ").strip()

from users.models import normalize_phone
normalized = normalize_phone(phone)
if not normalized:
    print("Invalid phone number — exiting.")
    raise SystemExit(1)

if TallyUser.objects.filter(phone_number=normalized).exists():
    print(f"User {normalized} already exists.")
else:
    TallyUser.objects.create_superuser(first_name=first_name, last_name=last_name, phone_number=normalized, password=password)
    print(f"\nSuperuser created: {normalized}")

print("\nSetup complete. Run the server with: uv run manage.py runserver")
