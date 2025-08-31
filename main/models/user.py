from django.contrib.auth.models import AbstractUser
from django.db import models
from .base import TimeStamped
import os
from uuid import uuid4


def avatar_upload_to(instance, filename):
    # Store as avatars/user_<id>/<uuid>.<ext> to avoid collisions
    base, ext = os.path.splitext(filename)
    ext = (ext or '').lower()
    user_id = getattr(instance, 'user_id', None) or 'anon'
    return f"avatars/user_{user_id}/{uuid4().hex}{ext}"

class CustomUser(AbstractUser):
    display_name = models.CharField(max_length=150, blank=True, default="")
    # Role: tutors can access tutor admin even if not staff
    is_tutor = models.BooleanField(default=False)

    def __str__(self):
        return self.display_name or self.username

class Profile(TimeStamped):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to=avatar_upload_to, blank=True, null=True)
    # Extended fields used by the Profiles page
    phone = models.CharField(max_length=50, blank=True, default="")
    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, default="")
    school = models.CharField(max_length=200, blank=True, default="")
    grade = models.CharField(max_length=50, blank=True, default="")
    academic_goals = models.TextField(blank=True, default="")
    language_pref = models.CharField(max_length=50, blank=True, default="")
    notification_pref = models.CharField(max_length=50, blank=True, default="")
    study_times = models.CharField(max_length=200, blank=True, default="")
    stream = models.CharField(max_length=50, blank=True, default="")
    learning_styles = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Profile({self.user.username})"

# Auto-create profile on user create
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=CustomUser)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
