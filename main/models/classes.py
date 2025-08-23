from django.db import models
from .base import TimeStamped
from .course import Course
from .user import CustomUser

class ClassSession(TimeStamped):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sessions")
    title = models.CharField(max_length=200)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)     # or meeting link
    capacity = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["starts_at"]
        indexes = [
            models.Index(fields=["starts_at"]),
        ]

    def __str__(self):
        return f"{self.course.title} – {self.title}"

class Reservation(TimeStamped):
    STATUS = (
        ("reserved", "Reserved"),
        ("attended", "Attended"),
        ("missed", "Missed"),
        ("cancelled", "Cancelled"),
    )
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, related_name="reservations")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reservations")
    status = models.CharField(max_length=20, choices=STATUS, default="reserved")

    class Meta:
        unique_together = ("session", "user")
        indexes = [
            models.Index(fields=["user", "session"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.user} – {self.session} ({self.status})"
