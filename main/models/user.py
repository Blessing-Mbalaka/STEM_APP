from django.contrib.auth.models import AbstractUser
from django.db import models
from .base import TimeStamped

class CustomUser(AbstractUser):
    display_name = models.CharField(max_length=150, blank=True, default="")

    def __str__(self):
        return self.display_name or self.username

class Profile(TimeStamped):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    def __str__(self):
        return f"Profile({self.user.username})"

# Auto-create profile on user create
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=CustomUser)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
