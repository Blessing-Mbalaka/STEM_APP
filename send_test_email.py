#!/usr/bin/env python
"""
Send Test Email to bjmbalaka@gmail.com
Tests actual SMTP email sending to Gmail
"""

import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stem_app.settings')
django.setup()

from django.core.mail import send_mail
from django.test import override_settings

print("\n" + "="*80)
print("SENDING TEST EMAIL TO bjmbalaka@gmail.com")
print("="*80 + "\n")

print("📧 Email Details:")
print(f"  From: {settings.DEFAULT_FROM_EMAIL}")
print(f"  To: bjmbalaka@gmail.com")
print(f"  Subject: STEM LMS - Test Email")
print()

# Try sending with SMTP backend (not console)
with override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'):
    try:
        print("Attempting to send email via SMTP...")
        print(f"  SMTP Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        print(f"  User: {settings.EMAIL_HOST_USER}")
        print(f"  TLS: {settings.EMAIL_USE_TLS}")
        print()
        
        subject = "STEM LMS - Test Email"
        message = """Hello,

This is a test email from the STEM LMS Application.

If you received this email, it means the SMTP email sending is working correctly!

Test Details:
- Timestamp: 2026-01-22
- Test Type: Direct SMTP send to bjmbalaka@gmail.com
- Status: SUCCESS

Please reply to this email if received.

Best regards,
STEM LMS Team
"""
        
        result = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            ['bjmbalaka@gmail.com'],
            fail_silently=False
        )
        
        print(f"✅ EMAIL SENT SUCCESSFULLY!")
        print(f"   Messages sent: {result}")
        print()
        print("📬 Check your inbox at bjmbalaka@gmail.com for the test email")
        print("   It may take a few moments to arrive")
        
    except Exception as e:
        print(f"❌ EMAIL SEND FAILED")
        print(f"   Error: {str(e)}")
        print()
        print("Possible reasons:")
        print("  • Gmail credentials invalid")
        print("  • Google App Password expired")
        print("  • Network/firewall blocking SMTP")
        print("  • Gmail account security settings")
        print()
        print("To fix:")
        print("  1. Verify Google App Password in settings.py")
        print("  2. Check Gmail security settings")
        print("  3. Enable 'Less secure app access' if needed")
        print("  4. Verify network allows port 587 outbound")

print()
print("="*80 + "\n")
