from django.db import models
from django.utils import timezone
from .base import TimeStamped
from .user import CustomUser
from .course import Course
from .classes import ClassSession


class Message(TimeStamped):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="messages_sent")
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="messages_received")
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    attachment = models.FileField(upload_to="message_attachments/%Y/%m/", blank=True, null=True)
    read_at = models.DateTimeField(blank=True, null=True)

    # Optional context
    related_course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name="messages")
    related_session = models.ForeignKey(ClassSession, on_delete=models.SET_NULL, null=True, blank=True, related_name="messages")

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_read(self) -> bool:
        return self.read_at is not None

    def mark_read(self):
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=["read_at"])

    def __str__(self):
        return f"{self.sender} -> {self.recipient}: {self.subject or self.body[:30]}"

