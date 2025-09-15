from __future__ import annotations

import os
from uuid import uuid4

from django.conf import settings
from django.db import models

from .base import TimeStamped, Slugged


def resource_upload_to(instance: "ResourceDocument", filename: str) -> str:
    base, ext = os.path.splitext(filename)
    ext = (ext or "").lower() or ".pdf"
    category_slug = getattr(instance.category, "slug", None) or "uncategorized"
    return f"resources/{category_slug}/{uuid4().hex}{ext}"


class ResourceCategory(TimeStamped, Slugged):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_resource_categories",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def _slug_source(self) -> str:
        return self.name


class ResourceDocument(TimeStamped):
    TERM_TERM1 = "term1"
    TERM_TERM2 = "term2"
    TERM_TERM3 = "term3"
    TERM_TERM4 = "term4"
    TERM_OTHER = "other"
    TERM_PAST_PAPERS = "past_papers"
    TERM_ATP = "atp"

    TERM_CHOICES = [
        (TERM_TERM1, "Term 1"),
        (TERM_TERM2, "Term 2"),
        (TERM_TERM3, "Term 3"),
        (TERM_TERM4, "Term 4"),
        (TERM_OTHER, "Supplementary"),
        (TERM_ATP, "Annual Teaching Plan"),
        (TERM_PAST_PAPERS, "Past Papers"),
    ]

    category = models.ForeignKey(
        ResourceCategory,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    term = models.CharField(max_length=20, choices=TERM_CHOICES, default=TERM_OTHER)
    file = models.FileField(upload_to=resource_upload_to)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_resource_documents",
    )
    original_filename = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title

    @classmethod
    def term_options(cls) -> list[dict[str, str]]:
        return [{"value": value, "label": label} for value, label in cls.TERM_CHOICES]

