from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("main", "0026_paid_classes_and_tutor_languages")]

    operations = [
        migrations.CreateModel(
            name="ChatbotAnswerCache",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("question_hash", models.CharField(max_length=64)),
                ("config_fingerprint", models.CharField(max_length=64)),
                ("answer", models.TextField()),
                ("sources", models.JSONField(blank=True, default=list)),
                ("hit_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_used_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Chatbot answer cache",
                "indexes": [
                    models.Index(
                        fields=["created_at"],
                        name="chatbot_cache_created_idx",
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("question_hash", "config_fingerprint"),
                        name="unique_chatbot_answer_cache",
                    ),
                ],
            },
        ),
    ]
