from django.contrib import admin
from .models import Game, Score, BracketCityScore, ConnectionsScore, WordleScore


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "order")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["order", "name"]


class BracketCityInline(admin.StackedInline):
    model = BracketCityScore
    extra = 0
    readonly_fields = ("total_score", "rank", "rank_emoji", "wrong_guesses", "peeks", "difficulty")


class WordleInline(admin.StackedInline):
    model = WordleScore
    extra = 0
    readonly_fields = ("puzzle_number", "attempts_grid", "attempts", "solved")


class ConnectionsInline(admin.StackedInline):
    model = ConnectionsScore
    extra = 0
    readonly_fields = ("puzzle_number", "attempts_grid", "wrong_guesses", "solved", "first_solved_category", "correct_categories")


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ("user", "game", "puzzle_date", "calculated_score", "game_identifier", "submitted_at")
    list_filter = ("game", "puzzle_date")
    search_fields = ("user__phone_number", "user__first_name", "user__last_name")
    ordering = ["-puzzle_date", "-submitted_at"]
    readonly_fields = ("submitted_at", "raw_text", "game_identifier")
    inlines = [BracketCityInline, ConnectionsInline, WordleInline]
