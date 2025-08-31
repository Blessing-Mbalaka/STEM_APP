from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0003_courseresource_thumbnail"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="phone",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        migrations.AddField(
            model_name="profile",
            name="dob",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="profile",
            name="gender",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.AddField(
            model_name="profile",
            name="school",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="profile",
            name="grade",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        migrations.AddField(
            model_name="profile",
            name="academic_goals",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="profile",
            name="language_pref",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        migrations.AddField(
            model_name="profile",
            name="notification_pref",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        migrations.AddField(
            model_name="profile",
            name="study_times",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="profile",
            name="stream",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        migrations.AddField(
            model_name="profile",
            name="learning_styles",
            field=models.JSONField(blank=True, null=True),
        ),
    ]

