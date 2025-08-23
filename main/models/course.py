from django.db import models
from .base import TimeStamped, Slugged
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
