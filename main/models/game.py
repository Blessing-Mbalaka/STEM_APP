from django.db import models
from .base import TimeStamped, Slugged
from .user import CustomUser

DIFFICULTY = (("easy","Easy"),("medium","Medium"),("hard","Hard"))

class Game(TimeStamped, Slugged):
    title = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)     # e.g., stem / steam / general
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY, blank=True)
    is_active = models.BooleanField(default=True)

    # NEW: quiz metadata
    duration_minutes = models.PositiveSmallIntegerField(default=15)    # matches JS "duration"
    max_points = models.PositiveSmallIntegerField(default=10)

    class Meta:
        indexes = [models.Index(fields=["is_active","category"])]

    def __str__(self):
        return self.title

# Question types the front-end supports (map your UI types to these)
QUESTION_TYPES = (
    ("multiple-choice","Multiple Choice"),
    ("true-false","True/False"),
    ("fill-blank","Fill in the Blank"),
    ("matching","Matching"),
    ("essay","Essay"),                   # graded as “answered” for now
    ("case-study","Case Study (MC)"),   # treated like multiple-choice
    ("calculation","Calculation"),
    ("chart-radar","Chart (Radar)"),
    ("chart-pie","Chart (Pie)"),
    ("chart-line","Chart (Line)"),
    ("chart-bar","Chart (Bar)"),
    ("chart-doughnut","Chart (Doughnut)"),
    ("chart-polar","Chart (Polar)"),
)

class GameQuestion(TimeStamped):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="questions")
    order = models.PositiveSmallIntegerField(default=1)
    qtype = models.CharField(max_length=32, choices=QUESTION_TYPES)
    question = models.TextField()

    # For MC/TF/fill/calculation/case-study/chart-* → use these
    options = models.JSONField(blank=True, null=True)           # list of strings for MC; ignored for TF
    correct_answer = models.JSONField(blank=True, null=True)    # number index / true|false / string / pairs list

    # For matching
    left_items = models.JSONField(blank=True, null=True)        # list[str]
    right_items = models.JSONField(blank=True, null=True)       # list[str]
    correct_matches = models.JSONField(blank=True, null=True)   # list[[left_idx,right_idx]]

    # For essay
    min_words = models.PositiveSmallIntegerField(blank=True, null=True)

    # For charts
    chart_data = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ["order","id"]

    def __str__(self):
        return f"{self.game.title} · Q{self.order}"
    

class GameScore(TimeStamped):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="game_scores")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="scores")
    score_percent = models.PositiveSmallIntegerField()          # 0–100
    points_awarded = models.PositiveSmallIntegerField(default=0)
    raw_answers = models.JSONField(blank=True, null=True)       # store submitted answers if you want

    class Meta:
        ordering = ["-created_at"]
