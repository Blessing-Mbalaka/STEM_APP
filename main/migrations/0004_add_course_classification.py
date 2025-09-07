from django.db import migrations, models


class Migration(migrations.Migration):

    # Chain after 0003 to avoid split heads
    dependencies = [
        ('main', '0003_fix_thread_is_locked_default'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='classification',
            field=models.CharField(max_length=20, blank=True),
        ),
    ]
