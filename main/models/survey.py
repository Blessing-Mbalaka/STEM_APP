from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .base import Slugged, TimeStamped

User = get_user_model()

SURVEY_QUESTION_TYPES: Tuple[Tuple[str, str], ...] = (
    ("short-text", "Short Text"),
    ("long-text", "Long Text"),
    ("single-choice", "Single Choice"),
    ("multi-choice", "Multiple Choice"),
    ("rating", "Rating"),
    ("number", "Numeric Input"),
    ("scale", "Scale (Slider)"),
    ("info", "Information Block"),
)

SURVEY_CHART_TYPES: Tuple[Tuple[str, str], ...] = (
    ("", "None"),
    ("bar", "Bar"),
    ("line", "Line"),
    ("radar", "Radar"),
    ("pie", "Pie"),
    ("doughnut", "Doughnut"),
)

PARTICIPANT_STATES: Tuple[Tuple[str, str], ...] = (
    ("pending", "Pending"),
    ("consented", "Consented"),
    ("dismissed", "Remind Later"),
    ("declined", "Declined"),
    ("completed", "Completed"),
)


def _validate_json_list(value: Any) -> None:
    if value in (None, "", []):
        return
    if not isinstance(value, list):
        raise ValidationError("Value must be a list.")


class CustomUserSurvey(TimeStamped, Slugged):
    """
    High-level survey configuration that can be toggled active by admins.
    """

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    intro_text = models.TextField(blank=True)
    outro_text = models.TextField(blank=True)
    consent_text = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)
    require_consent = models.BooleanField(default=True)
    target_roles = models.JSONField(blank=True, default=list, validators=[_validate_json_list])
    display_rules = models.JSONField(blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="surveys_created",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "created_at"]),
        ]

    def __str__(self) -> str:
        return self.title

    def allows_role(self, role: str) -> bool:
        roles = self.target_roles or []
        return not roles or role in roles


class CustomUserSurveyQuestion(TimeStamped):
    """
    Question belonging to a survey. Configuration is stored in JSON so the
    builder UI has freedom to persist option lists, slider config, etc.
    """

    survey = models.ForeignKey(
        CustomUserSurvey,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    order = models.PositiveIntegerField(default=1)
    qtype = models.CharField(max_length=32, choices=SURVEY_QUESTION_TYPES)
    prompt = models.TextField()
    help_text = models.TextField(blank=True)
    is_required = models.BooleanField(default=True)
    is_scored = models.BooleanField(default=False)
    max_score = models.FloatField(default=0)
    chart_type = models.CharField(max_length=16, choices=SURVEY_CHART_TYPES, blank=True, default="")
    config = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ["order", "id"]
        indexes = [
            models.Index(fields=["survey", "order"]),
        ]
        unique_together = ("survey", "order")

    def __str__(self) -> str:
        return f"{self.survey.title} · Q{self.order}"

    def option_scores(self) -> Dict[str, float]:
        options = (self.config or {}).get("options", [])
        if not isinstance(options, list):
            return {}
        result: Dict[str, float] = {}
        for opt in options:
            if not isinstance(opt, dict):
                continue
            value = str(opt.get("value", "")).strip()
            if not value:
                continue
            try:
                score = float(opt.get("score", 0))
            except (TypeError, ValueError):
                score = 0.0
            result[value] = score
        return result

    def option_labels(self) -> Dict[str, str]:
        options = (self.config or {}).get("options", [])
        labels: Dict[str, str] = {}
        for opt in options:
            if not isinstance(opt, dict):
                continue
            value = str(opt.get("value", "")).strip()
            if not value:
                continue
            labels[value] = str(opt.get("label") or opt.get("text") or value)
        return labels

    def normalised_max_score(self) -> float:
        if self.max_score > 0:
            return float(self.max_score)
        if self.qtype in {"single-choice", "multi-choice"}:
            scores = self.option_scores().values()
            if self.qtype == "single-choice":
                return float(max(scores, default=0))
            return float(sum(score for score in scores if score > 0))
        return 100.0 if self.is_scored else 0.0


class CustomUserSurveyParticipant(TimeStamped):
    """
    Tracks the state of a user relative to a survey (prompted, consented, etc).
    """

    survey = models.ForeignKey(
        CustomUserSurvey,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="survey_participation",
    )
    status = models.CharField(max_length=16, choices=PARTICIPANT_STATES, default="pending")
    consented_at = models.DateTimeField(blank=True, null=True)
    dismissed_at = models.DateTimeField(blank=True, null=True)
    last_prompted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("survey", "user")
        indexes = [
            models.Index(fields=["survey", "status"]),
        ]

    def mark_prompted(self) -> None:
        self.last_prompted_at = timezone.now()
        self.save(update_fields=["last_prompted_at", "updated_at"])


class CustomUserSurveyResponse(TimeStamped):
    """
    Stores submitted answers and optional score summary for a participant.
    """

    participant = models.OneToOneField(
        CustomUserSurveyParticipant,
        on_delete=models.CASCADE,
        related_name="response",
    )
    answers = models.JSONField()
    score_summary = models.JSONField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]

    @property
    def survey(self) -> CustomUserSurvey:
        return self.participant.survey

    @property
    def user(self) -> User:
        return self.participant.user
