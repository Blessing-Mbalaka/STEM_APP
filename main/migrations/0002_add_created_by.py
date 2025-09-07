from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='courses_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='game',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='games_created', to=settings.AUTH_USER_MODEL),
        ),
    ]

