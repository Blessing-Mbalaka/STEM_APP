from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0007_courseresource_poll_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='is_tutor',
            field=models.BooleanField(default=False),
        ),
    ]

