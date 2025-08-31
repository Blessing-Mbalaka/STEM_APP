from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0006_courseresource_quiz_position"),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseresource',
            name='resource_type',
            field=models.CharField(blank=True, choices=[('video', 'Video'), ('youtube', 'YouTube'), ('audio', 'Audio'), ('document', 'Document'), ('link', 'Link'), ('quiz', 'Quiz'), ('poll', 'Poll')], help_text='Type of resource', max_length=50),
        ),
        migrations.AddField(
            model_name='courseresource',
            name='poll_question',
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name='courseresource',
            name='poll_options',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='courseresource',
            name='poll_multi',
            field=models.BooleanField(default=False),
        ),
    ]

