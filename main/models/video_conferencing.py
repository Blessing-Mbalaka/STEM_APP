from django.db import models
from .user import CustomUser
from django.utils import timezone
from datetime import timedelta



class Session(models.Model):
    title = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    duration_minutes = models.IntegerField()
    scheduled_time = models.DateTimeField()
    tutor = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    def can_start(self):
        # Example logic to determine if the session can start
        return timezone.now() >= self.scheduled_time - timedelta(minutes=5)