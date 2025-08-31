from django.db import models
from .base import TimeStamped, Slugged
from .game import Game
from .user import CustomUser

LEVEL = (
    ("intro", "Introductory"),
    ("intermediate", "Intermediate"),
    ("advanced", "Advanced"),
)

class Course(TimeStamped, Slugged):
    title = models.CharField(max_length=200, unique=True)
    summary = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    subject = models.CharField(max_length=120, blank=True)     # e.g., Physics
    level = models.CharField(max_length=20, choices=LEVEL, blank=True)
    thumbnail = models.ImageField(upload_to="course_thumbs/", blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_active", "subject", "level"]),
        ]

    def __str__(self):
        return self.title


# Resource model for YouTube/video links
class CourseResource(TimeStamped):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="resources")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    resource_type = models.CharField(max_length=50, choices=[
        ('video', 'Video'),
        ('youtube', 'YouTube'),
        ('audio', 'Audio'),
        ('document', 'Document'),
        ('link', 'Link'),
        ('quiz', 'Quiz'),
        ('poll', 'Poll'),
    ], blank=True, help_text="Type of resource")
    url = models.URLField(blank=True, help_text='For YouTube or external links')
    file = models.FileField(upload_to='course_resources/', blank=True, null=True, help_text='For uploaded files')
    learning_style = models.CharField(max_length=20, choices=[
        ('visual', 'Visual'),
        ('auditory', 'Auditory'),
        ('readwrite', 'Read/Write')
    ], default='visual')

    # Optional link to a Game when resource_type == 'quiz'
    game = models.ForeignKey(Game, on_delete=models.SET_NULL, null=True, blank=True, related_name='course_resources')

    # Ordering within a course
    position = models.PositiveIntegerField(default=0)

    # Poll data when resource_type == 'poll'
    poll_question = models.CharField(max_length=300, blank=True)
    poll_options = models.JSONField(blank=True, null=True)
    poll_multi = models.BooleanField(default=False)

    thumbnail = models.ImageField(
        upload_to="course_resource_thumbs/",
        blank=True, null=True,
        help_text="Optional cover/thumbnail image shown in the UI"
    )

    def __str__(self):
        return f"{self.title} ({self.resource_type})"

    class Meta:
        ordering = ["position", "created_at", "id"]

class Enrollment(TimeStamped):
    ENROLL_STATUS = (
        ("enrolled", "Enrolled"),
        ("completed", "Completed"),
        ("dropped", "Dropped"),
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=20, choices=ENROLL_STATUS, default="enrolled")
    progress = models.PositiveSmallIntegerField(default=0)  # 0–100

    class Meta:
        unique_together = ("user", "course")
        indexes = [
            models.Index(fields=["user", "course"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.user} -> {self.course} ({self.status}, {self.progress}%)"
