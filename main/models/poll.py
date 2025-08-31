from django.db import models
from .user import CustomUser
from .course import CourseResource
from .base import TimeStamped


class CoursePollVote(TimeStamped):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='poll_votes')
    resource = models.ForeignKey(CourseResource, on_delete=models.CASCADE, related_name='votes')
    # store indices of selected options
    choices = models.JSONField()

    class Meta:
        unique_together = ("user", "resource")

    def __str__(self):
        return f"{self.user} -> poll {self.resource_id}: {self.choices}"

