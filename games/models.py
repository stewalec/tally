from django.db import models
from django.conf import settings


class Game(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    url = models.URLField("URL", blank=True, help_text="Link to the online playable game")
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0, help_text="Display order in the UI")

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Score(models.Model):
    """Generic score record — one per user per puzzle."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="scores")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="scores")
    raw_text = models.TextField(help_text="Original SMS text that was submitted")
    calculated_score = models.FloatField(help_text="Normalized numeric score for comparisons")
    puzzle_date = models.DateField(help_text="Eastern-time date of the puzzle")
    # game_identifier is a stable, unique key for the puzzle (date string for Bracket City,
    # puzzle number string for Connections).  Used for the duplicate-submission check.
    game_identifier = models.CharField(max_length=50)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "game", "game_identifier")]
        ordering = ["-puzzle_date"]

    def __str__(self):
        return f"{self.user} – {self.game} – {self.puzzle_date}"


class BracketCityScore(models.Model):
    score = models.OneToOneField(Score, on_delete=models.CASCADE, related_name="bracket_city_detail")
    total_score = models.FloatField()
    rank = models.CharField(max_length=100, blank=True)
    rank_emoji = models.CharField(max_length=10, blank=True)
    wrong_guesses = models.PositiveSmallIntegerField(default=0)
    peeks = models.PositiveSmallIntegerField(default=0)
    difficulty = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"BC {self.total_score} ({self.difficulty})"


class ConnectionsScore(models.Model):
    score = models.OneToOneField(Score, on_delete=models.CASCADE, related_name="connections_detail")
    puzzle_number = models.PositiveIntegerField()
    attempts_grid = models.JSONField(help_text="List of rows; each row is a list of color names")
    wrong_guesses = models.PositiveSmallIntegerField(default=0)
    solved = models.BooleanField(default=False)
    first_solved_category = models.CharField(max_length=20, blank=True)
    correct_categories = models.JSONField(default=list, help_text="Ordered list of solved category colors")

    def __str__(self):
        return f"Connections #{self.puzzle_number} ({'solved' if self.solved else 'unsolved'})"
