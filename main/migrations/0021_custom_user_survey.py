from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0020_chatbotconfig'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomUserSurvey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('slug', models.SlugField(blank=True, max_length=220, unique=True)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('intro_text', models.TextField(blank=True)),
                ('outro_text', models.TextField(blank=True)),
                ('consent_text', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=False)),
                ('require_consent', models.BooleanField(default=True)),
                ('target_roles', models.JSONField(blank=True, default=list)),
                ('display_rules', models.JSONField(blank=True, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='surveys_created', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['is_active', 'created_at'], name='main_custom_is_acti_01a86f_idx')],
            },
        ),
        migrations.CreateModel(
            name='CustomUserSurveyQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order', models.PositiveIntegerField(default=1)),
                ('qtype', models.CharField(choices=[('short-text', 'Short Text'), ('long-text', 'Long Text'), ('single-choice', 'Single Choice'), ('multi-choice', 'Multiple Choice'), ('rating', 'Rating'), ('number', 'Numeric Input'), ('scale', 'Scale (Slider)'), ('info', 'Information Block')], max_length=32)),
                ('prompt', models.TextField()),
                ('help_text', models.TextField(blank=True)),
                ('is_required', models.BooleanField(default=True)),
                ('is_scored', models.BooleanField(default=False)),
                ('max_score', models.FloatField(default=0)),
                ('chart_type', models.CharField(blank=True, choices=[('', 'None'), ('bar', 'Bar'), ('line', 'Line'), ('radar', 'Radar'), ('pie', 'Pie'), ('doughnut', 'Doughnut')], default='', max_length=16)),
                ('config', models.JSONField(blank=True, null=True)),
                ('survey', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='main.customusersurvey')),
            ],
            options={
                'ordering': ['order', 'id'],
                'indexes': [models.Index(fields=['survey', 'order'], name='main_custom_survey__798f1d_idx')],
                'unique_together': {('survey', 'order')},
            },
        ),
        migrations.CreateModel(
            name='CustomUserSurveyParticipant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('consented', 'Consented'), ('dismissed', 'Remind Later'), ('declined', 'Declined'), ('completed', 'Completed')], default='pending', max_length=16)),
                ('consented_at', models.DateTimeField(blank=True, null=True)),
                ('dismissed_at', models.DateTimeField(blank=True, null=True)),
                ('last_prompted_at', models.DateTimeField(blank=True, null=True)),
                ('survey', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='main.customusersurvey')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='survey_participation', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['survey', 'status'], name='main_custom_survey__d47e6a_idx')],
                'unique_together': {('survey', 'user')},
            },
        ),
        migrations.CreateModel(
            name='CustomUserSurveyResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('answers', models.JSONField()),
                ('score_summary', models.JSONField(blank=True, null=True)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('participant', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='response', to='main.customusersurveyparticipant')),
            ],
            options={
                'ordering': ['-submitted_at'],
            },
        ),
    ]
