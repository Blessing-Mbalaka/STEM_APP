# Add these to your main/models.py
from django.db import models
from django.contrib.auth.models import User

class ChatbotConversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

class ChatbotResponse(models.Model):
    RESPONSE_TYPES = [
        ('rag', 'RAG Knowledge Base'),
        ('cached', 'Cached Response'),
        ('internet_search', 'Internet Search'),
        ('no_knowledge', 'No Knowledge Found'),
    ]
    
    conversation = models.ForeignKey(ChatbotConversation, on_delete=models.CASCADE)
    response = models.TextField()
    sources = models.TextField(blank=True)  # JSON string
    response_type = models.CharField(max_length=20, choices=RESPONSE_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

class ChatbotCache(models.Model):
    question_hash = models.CharField(max_length=32, db_index=True)
    question = models.TextField()
    answer = models.TextField()
    sources = models.TextField(blank=True)  # JSON string
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['question_hash', 'created_at']),
        ]

class PDFDocument(models.Model):
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='pdfs/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class PDFChunk(models.Model):
    document = models.ForeignKey(PDFDocument, on_delete=models.CASCADE)
    content = models.TextField()
    page_number = models.IntegerField()
    chunk_index = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)