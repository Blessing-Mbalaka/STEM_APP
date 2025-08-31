from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0009_coursepollvote"),
    ]

    operations = [
        migrations.AddField(
            model_name='classsession',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='classes_created', to='main.customuser'),
        ),
    ]

