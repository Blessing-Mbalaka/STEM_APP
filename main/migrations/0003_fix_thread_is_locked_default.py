from django.db import migrations, models


class Migration(migrations.Migration):

    # Make this depend on the latest existing migration to avoid a split graph
    dependencies = [
        ('main', '0014_merge_0002_add_created_by_0013_game_points'),
    ]

    operations = [
        migrations.AlterField(
            model_name='thread',
            name='is_locked',
            field=models.BooleanField(default=False),
        ),
    ]
