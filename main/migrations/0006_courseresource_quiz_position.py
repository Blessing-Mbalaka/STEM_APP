from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0005_profile_avatar_unique_path"),
    ]

    operations = [
        migrations.AddField(
            model_name='courseresource',
            name='game',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='course_resources', to='main.game'),
        ),
        migrations.AddField(
            model_name='courseresource',
            name='position',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='courseresource',
            name='resource_type',
            field=models.CharField(blank=True, choices=[('video', 'Video'), ('youtube', 'YouTube'), ('audio', 'Audio'), ('document', 'Document'), ('link', 'Link'), ('quiz', 'Quiz')], help_text='Type of resource', max_length=50),
        ),
    ]

