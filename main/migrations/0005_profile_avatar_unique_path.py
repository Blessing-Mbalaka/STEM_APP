from django.db import migrations, models
import main.models.user


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0004_profile_extended_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to=main.models.user.avatar_upload_to),
        ),
    ]

