from django.db import models
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

class Message(TimeStamped):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    session = models.ForeignKey(TutorSession, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Message from {self.sender.email} to {self.recipient.email}: {self.subject}"