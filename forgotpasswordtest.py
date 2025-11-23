# forgotpasswordtest.py
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stem_app.settings')
django.setup()

from django.core.mail import send_mail

# Simulate forgot password email
send_mail(
    'Password Reset Request',
    'Click the link below to reset your password: http://example.com/reset/',
    'stemappza@gmail.com',
    ['bjmbalaka@gmail.com'],
    fail_silently=False,
)
print("Test email sent."