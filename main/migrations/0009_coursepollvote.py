from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0008_customuser_is_tutor"),
    ]

    operations = [
        migrations.CreateModel(
            name='CoursePollVote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('choices', models.JSONField()),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='main.courseresource')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='poll_votes', to='main.customuser')),
            ],
            options={'abstract': False},
        ),
        migrations.AlterUniqueTogether(
            name='coursepollvote',
            unique_together={("user", "resource")},
        ),
    ]

