from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0019_badge_userbadge"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChatbotConfig",
            fields=[
                (
                    "id",
                    models.PositiveSmallIntegerField(
                        default=1,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("is_enabled", models.BooleanField(default=True)),
                (
                    "mode",
                    models.CharField(
                        choices=[
                            ("gemini", "Gemini (default)"),
                            ("external", "External REST API"),
                            ("ollama", "Ollama (local server)"),
                        ],
                        default="gemini",
                        max_length=20,
                    ),
                ),
                (
                    "allow_internet_search",
                    models.BooleanField(
                        default=True,
                        help_text="If disabled, the chatbot will skip any internet search steps.",
                    ),
                ),
                (
                    "maintenance_message",
                    models.TextField(
                        default="Our AI assistant is currently undergoing maintenance. Please post your question in the forum and the next available tutor will respond.",
                    ),
                ),
                ("external_api_base_url", models.URLField(blank=True)),
                ("external_api_key", models.CharField(blank=True, max_length=255)),
                ("external_model", models.CharField(blank=True, max_length=120)),
                (
                    "ollama_api_base_url",
                    models.URLField(
                        blank=True, help_text="e.g. http://localhost:11434"
                    ),
                ),
                (
                    "ollama_model",
                    models.CharField(
                        blank=True,
                        help_text="e.g. llama3:latest",
                        max_length=120,
                    ),
                ),
                (
                    "gemini_model",
                    models.CharField(
                        blank=True,
                        help_text="Optional override for the Gemini model when using the default mode.",
                        max_length=120,
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Chatbot configuration",
            },
        ),
    ]
