from __future__ import annotations

import os
from uuid import uuid4

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .base import TimeStamped
from .user import CustomUser

class TutorSession(TimeStamped):
    tutor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='tutor_sessions')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='student_sessions')
    title = models.CharField(max_length=200)
    description = models.TextField()
    subject = models.CharField(max_length=100)
    scheduled_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    meeting_link = models.URLField(blank=True, null=True)
    meeting_id = models.CharField(max_length=100, blank=True, null=True)
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    class Meta:
        ordering = ['-scheduled_time']
        
    def __str__(self):
        return f"{self.title} - {self.student.email} with {self.tutor.email}"

def tutor_document_upload_to(instance: "TutorApplicationDocument", filename: str) -> str:
    base, ext = os.path.splitext(filename)
    ext = (ext or "").lower() or ".pdf"
    user_id = instance.application.user_id if instance.application_id else "pending"
    return f"tutor_applications/user_{user_id}/{uuid4().hex}{ext}"


class TutorApplication(TimeStamped):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_PENDING, _("Pending")),
        (STATUS_APPROVED, _("Approved")),
        (STATUS_REJECTED, _("Rejected")),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tutor_application",
    )
    motivation = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_tutor_applications",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"TutorApplication(user={self.user.username}, status={self.status})"


class TutorApplicationDocument(TimeStamped):
    DOC_ID = "id"
    DOC_QUALIFICATION = "qualification"
    DOC_SUPPORTING = "supporting"
    DOC_SACE = "sace"

    DOC_CHOICES = [
        (DOC_ID, _("Identity Document")),
        (DOC_QUALIFICATION, _("Qualification")),
        (DOC_SUPPORTING, _("Supporting")),
        (DOC_SACE, _("SACE Certificate")),
    ]

    application = models.ForeignKey(
        TutorApplication,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    file = models.FileField(upload_to=tutor_document_upload_to)
    original_name = models.CharField(max_length=255, blank=True)
    doc_type = models.CharField(max_length=20, choices=DOC_CHOICES, default=DOC_SUPPORTING)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        name = self.original_name or os.path.basename(self.file.name)
        return f"Document({name})"


class TutorMessage(TimeStamped):
    tutor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="tutor_messages_sent")
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="tutor_messages_received")
    subject = models.CharField(max_length=200)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    session = models.ForeignKey(TutorSession, on_delete=models.CASCADE, related_name="messages", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Message from {self.tutor.email} to {self.recipient.email}: {self.subject}"
