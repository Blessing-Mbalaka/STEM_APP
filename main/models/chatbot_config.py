from __future__ import annotations

from django.db import models


class ChatbotConfig(models.Model):
    """Singleton storing runtime configuration for the forum chatbot."""

    SINGLETON_PK = 1

    MODE_GEMINI = "gemini"
    MODE_EXTERNAL = "external"
    MODE_OLLAMA = "ollama"

    MODE_CHOICES = [
        (MODE_GEMINI, "Gemini (default)"),
        (MODE_EXTERNAL, "External REST API"),
        (MODE_OLLAMA, "Ollama (local server)"),
    ]

    id = models.PositiveSmallIntegerField(
        primary_key=True,
        default=SINGLETON_PK,
        editable=False,
    )
    is_enabled = models.BooleanField(default=True)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=MODE_GEMINI)
    allow_internet_search = models.BooleanField(
        default=True,
        help_text="If disabled, the chatbot will skip any internet search steps.",
    )
    maintenance_message = models.TextField(
        default=(
            "Our AI assistant is currently undergoing maintenance. "
            "Please post your question in the forum and the next available tutor will respond."
        ),
    )

    # External API configuration
    external_api_base_url = models.URLField(blank=True)
    external_api_key = models.CharField(max_length=255, blank=True)
    external_model = models.CharField(max_length=120, blank=True)

    # Ollama configuration
    ollama_api_base_url = models.URLField(blank=True, help_text="e.g. http://localhost:11434")
    ollama_model = models.CharField(max_length=120, blank=True, help_text="e.g. llama3:latest")

    gemini_model = models.CharField(
        max_length=120,
        blank=True,
        help_text="Optional override for the Gemini model when using the default mode.",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Chatbot configuration"

    def save(self, *args, **kwargs):
        self.pk = self.SINGLETON_PK
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "ChatbotConfig":
        obj, _ = cls.objects.get_or_create(
            pk=cls.SINGLETON_PK,
            defaults={
                "maintenance_message": cls._meta.get_field("maintenance_message").default,
            },
        )
        return obj

    def as_dict(self, *, include_sensitive: bool = False) -> dict:
        payload = {
            "is_enabled": self.is_enabled,
            "mode": self.mode,
            "allow_internet_search": self.allow_internet_search,
            "maintenance_message": self.maintenance_message,
            "external_api_base_url": self.external_api_base_url,
            "external_model": self.external_model,
            "ollama_api_base_url": self.ollama_api_base_url,
            "ollama_model": self.ollama_model,
            "gemini_model": self.gemini_model,
            "updated_at": self.updated_at.isoformat() if self.updated_at else "",
        }
        if include_sensitive:
            payload["external_api_key"] = self.external_api_key
        return payload


class ChatbotAnswerCache(models.Model):
    """Persistent cache of provider answers for exact, non-personalised questions."""

    question_hash = models.CharField(max_length=64)
    config_fingerprint = models.CharField(max_length=64)
    answer = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    hit_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["question_hash", "config_fingerprint"],
                name="unique_chatbot_answer_cache",
            ),
        ]
        indexes = [
            models.Index(fields=["created_at"], name="chatbot_cache_created_idx"),
        ]
        verbose_name = "Chatbot answer cache"
