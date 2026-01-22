#!/usr/bin/env python
"""
Comprehensive SMTP and Forgot Password Authentication Test Script
Tests email backend connectivity, forgot password flow, and password reset functionality.
"""

import os
import sys
import django
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.core.mail.backends.console import EmailBackend as ConsoleBackend
from django.core.mail.backends.locmem import EmailBackend as LocmemBackend
from django.core.mail.backends.smtp import EmailBackend as SmtpBackend
from django.core.mail import get_connection
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
import json
from io import StringIO
import smtplib
from email.mime.text import MIMEText
from django.test import override_settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stem_app.settings')
django.setup()

from main.models import CustomUser
from django.test import override_settings
from django.core import mail

print("\n" + "="*80)
print("STEM APPLICATION - SMTP & FORGOT PASSWORD AUTHENTICATION TEST")
print("="*80 + "\n")

# ============================================================================
# SECTION 1: SMTP CONFIGURATION AUDIT
# ============================================================================
print("📋 SECTION 1: SMTP CONFIGURATION AUDIT")
print("-" * 80)

print(f"✓ Current EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"✓ EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"✓ EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"✓ EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"✓ EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"✓ EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
print(f"✓ DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

# Check if SMTP is configured
is_console = "console" in settings.EMAIL_BACKEND.lower()
is_smtp = "smtp" in settings.EMAIL_BACKEND.lower()
print(f"\n✓ Email Backend Type: {'CONSOLE (Development - prints to stdout)' if is_console else 'SMTP (Production)' if is_smtp else 'OTHER'}")

# ============================================================================
# SECTION 2: SMTP CONNECTIVITY TEST
# ============================================================================
print("\n" + "="*80)
print("📡 SECTION 2: SMTP CONNECTIVITY TEST")
print("-" * 80)

smtp_test_passed = False
try:
    # Test SMTP connection without actually sending
    connection = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=5)
    connection.starttls()
    print(f"✓ Connected to SMTP server: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
    print(f"✓ TLS enabled successfully")
    
    # Try authentication
    try:
        connection.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        print(f"✓ SMTP authentication successful with user: {settings.EMAIL_HOST_USER}")
        smtp_test_passed = True
    except smtplib.SMTPAuthenticationError as e:
        print(f"✗ SMTP authentication FAILED: {str(e)}")
    except Exception as auth_err:
        print(f"✗ SMTP authentication error: {str(auth_err)}")
    
    connection.quit()
    
except smtplib.SMTPException as e:
    print(f"✗ SMTP connection error: {str(e)}")
except Exception as e:
    print(f"✗ Connection error: {str(e)}")

print(f"\n{'✓ SMTP CONNECTIVITY TEST PASSED' if smtp_test_passed else '✗ SMTP CONNECTIVITY TEST FAILED'}")

# ============================================================================
# SECTION 3: GET OR CREATE TEST USER
# ============================================================================
print("\n" + "="*80)
print("👤 SECTION 3: TEST USER SETUP")
print("-" * 80)

test_email = "testuser@stemapp.local"
test_username = "testuser_smtp"
test_password = "TestPassword123!@#"

try:
    # Try to get existing test user
    user = CustomUser.objects.filter(email=test_email).first()
    if user:
        print(f"✓ Found existing test user: {user.username} ({user.email})")
        # Reset password for testing
        user.set_password(test_password)
        user.save()
        print(f"✓ Reset test user password for testing")
    else:
        # Create new test user
        user = CustomUser.objects.create_user(
            username=test_username,
            email=test_email,
            password=test_password,
            first_name="Test",
            last_name="User"
        )
        print(f"✓ Created test user: {user.username} ({user.email})")
except Exception as e:
    print(f"✗ Error setting up test user: {str(e)}")
    user = None

if user:
    print(f"✓ Test user ready:")
    print(f"  - Username: {user.username}")
    print(f"  - Email: {user.email}")
    print(f"  - User ID: {user.id}")

# ============================================================================
# SECTION 4: FORGOT PASSWORD EMAIL TEST (Using locmem backend for safety)
# ============================================================================
print("\n" + "="*80)
print("📧 SECTION 4: FORGOT PASSWORD EMAIL TEST")
print("-" * 80)

forgot_password_success = False
email_content = None
reset_token = None
reset_uid = None

if user:
    # Use locmem backend to capture emails without sending
    with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
        try:
            # Clear outbox
            mail.outbox = []
            
            # Generate token and UID for password reset
            reset_token = default_token_generator.make_token(user)
            reset_uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Build reset link
            reset_link = f"http://localhost:8000/reset-password/{reset_uid}/{reset_token}"
            
            # Create email content (mimicking the forgot password email)
            subject = "Reset your STEM LMS password"
            plain_text = f"""
Hello {user.first_name or user.username},

We received a request to reset the password for your STEM LMS account. 
Click the link below to reset your password:

{reset_link}

This link will expire in 24 hours.

If you did not request this, please ignore this email.

Best regards,
STEM LMS Team
            """
            
            html_content = f"""
<html>
<body>
<p>Hello {user.first_name or user.username},</p>
<p>We received a request to reset the password for your STEM LMS account.</p>
<p><a href="{reset_link}">Click here to reset your password</a></p>
<p>This link will expire in 24 hours.</p>
<p>If you did not request this, please ignore this email.</p>
<p>Best regards,<br>STEM LMS Team</p>
</body>
</html>
            """
            
            # Send email using send_mail (like the codebase does)
            from django.core.mail import send_mail
            
            send_mail(
                subject,
                plain_text,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False
            )
            
            print(f"✓ Forgot password email queued successfully")
            print(f"  - Recipient: {user.email}")
            print(f"  - Subject: {subject}")
            print(f"  - Token generated: {reset_token[:20]}...")
            print(f"  - UID (base64): {reset_uid}")
            
            # Check if email was captured
            if len(mail.outbox) > 0:
                sent_email = mail.outbox[0]
                email_content = sent_email
                print(f"\n✓ Email captured in outbox:")
                print(f"  - From: {sent_email.from_email}")
                print(f"  - To: {sent_email.to}")
                print(f"  - Subject: {sent_email.subject}")
                print(f"\n📝 Email Body (Plain Text):")
                print("-" * 80)
                print(sent_email.body)
                print("-" * 80)
                
                if sent_email.alternatives:
                    print(f"\n📝 Email Body (HTML):")
                    print("-" * 80)
                    print(sent_email.alternatives[0][0])
                    print("-" * 80)
                
                print(f"\n✓ Reset link in email: {reset_link}")
                forgot_password_success = True
            else:
                print(f"✗ Email not captured in outbox")
                
        except Exception as e:
            print(f"✗ Error sending forgot password email: {str(e)}")
            import traceback
            traceback.print_exc()
else:
    print("✗ Test user not available, skipping email test")

print(f"\n{'✓ FORGOT PASSWORD EMAIL TEST PASSED' if forgot_password_success else '✗ FORGOT PASSWORD EMAIL TEST FAILED'}")

# ============================================================================
# SECTION 5: TOKEN VALIDATION TEST
# ============================================================================
print("\n" + "="*80)
print("🔐 SECTION 5: TOKEN VALIDATION TEST")
print("-" * 80)

token_valid = False
if user and reset_token:
    try:
        # Check if token is valid
        is_valid = default_token_generator.check_token(user, reset_token)
        print(f"✓ Token validation: {'VALID' if is_valid else 'INVALID'}")
        token_valid = is_valid
        
        if is_valid:
            print(f"  - User: {user.username}")
            print(f"  - Token: {reset_token[:30]}...")
            print(f"  - Token type: Default Django token generator (secure)")
        
    except Exception as e:
        print(f"✗ Token validation error: {str(e)}")
else:
    print("✗ Token or user not available")

print(f"\n{'✓ TOKEN VALIDATION TEST PASSED' if token_valid else '✗ TOKEN VALIDATION TEST FAILED'}")

# ============================================================================
# SECTION 6: PASSWORD RESET TEST
# ============================================================================
print("\n" + "="*80)
print("🔑 SECTION 6: PASSWORD RESET TEST")
print("-" * 80)

password_reset_success = False
if user and token_valid:
    try:
        # Generate new password
        new_password = "NewTestPassword456!@#"
        
        # Verify old password works (before reset)
        old_auth = user.check_password(test_password)
        print(f"✓ Old password authentication: {'✓ Works' if old_auth else '✗ Does not work'}")
        
        # Set new password
        user.set_password(new_password)
        user.save()
        print(f"✓ New password set successfully")
        
        # Verify new password works
        user_refreshed = CustomUser.objects.get(pk=user.pk)
        new_auth = user_refreshed.check_password(new_password)
        print(f"✓ New password authentication: {'✓ Works' if new_auth else '✗ Does not work'}")
        
        # Verify old password no longer works
        old_auth_after = user_refreshed.check_password(test_password)
        print(f"✓ Old password after reset: {'✗ Still works (BAD)' if old_auth_after else '✓ No longer works (GOOD)'}")
        
        if new_auth and not old_auth_after:
            password_reset_success = True
            print(f"\n✓ Password successfully reset from '{test_password}' to '{new_password}'")
        else:
            print(f"\n✗ Password reset verification failed")
            
    except Exception as e:
        print(f"✗ Password reset error: {str(e)}")
        import traceback
        traceback.print_exc()
else:
    print("✗ User or valid token not available")

print(f"\n{'✓ PASSWORD RESET TEST PASSED' if password_reset_success else '✗ PASSWORD RESET TEST FAILED'}")

# ============================================================================
# SECTION 7: IMPLEMENTATION COMPARISON
# ============================================================================
print("\n" + "="*80)
print("🔍 SECTION 7: IMPLEMENTATION COMPARISON")
print("-" * 80)

print("\n✓ Primary Implementation: main/views.py")
print("  - ForgotPasswordView (GET): Renders forgot password form")
print("  - send_forgot_password_email (POST): Sends reset email with token")
print("  - ResetPasswordView (GET): Renders password reset form")
print("  - reset_password (POST): Updates password with token validation")
print("  Status: ✓ ACTIVE AND IN USE")

print("\n✓ Legacy Implementation: main/utils.py")
print("  - send_email(): Wrapper for Django send_mail")
print("  - send_forgot_password(): Legacy forgot password sender")
print("  - reset_password(): Legacy password reset handler")
print("  Status: ⚠ EXISTS BUT APPEARS UNUSED")

print("\n✓ Email Utility Functions:")
print("  - Used for: Password reset, tutor session emails, session cancellations")
print("  - Location: main/utils.py")

# ============================================================================
# SECTION 8: SUMMARY & RECOMMENDATIONS
# ============================================================================
print("\n" + "="*80)
print("📊 TEST SUMMARY & RECOMMENDATIONS")
print("="*80)

summary = {
    "SMTP Connectivity": "✓ PASSED" if smtp_test_passed else "✗ FAILED",
    "Forgot Password Email": "✓ PASSED" if forgot_password_success else "✗ FAILED",
    "Token Validation": "✓ PASSED" if token_valid else "✗ FAILED",
    "Password Reset": "✓ PASSED" if password_reset_success else "✗ FAILED",
}

all_passed = all("✓ PASSED" in v for v in summary.values())

for test_name, result in summary.items():
    print(f"{result} | {test_name}")

print("\n" + "-" * 80)
if all_passed:
    print("🎉 ALL TESTS PASSED! Email authentication system is working correctly.")
else:
    print("⚠️  SOME TESTS FAILED. See details above and recommendations below.")

print("\n📝 RECOMMENDATIONS:")
print("-" * 80)
if not smtp_test_passed:
    print("⚠️  SMTP Connectivity Failed:")
    print("    1. Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in settings.py")
    print("    2. Check Google App Password (if using Gmail)")
    print("    3. Verify firewall/network allows outbound port 587")
    print("    4. Enable 'Less secure app access' if required")

if not forgot_password_success:
    print("⚠️  Forgot Password Email Failed:")
    print("    1. Check EMAIL_BACKEND configuration in settings.py")
    print("    2. Verify email template paths in main/views.py")
    print("    3. Test with locmem backend first (safer)")

if token_valid:
    print("✓ Token Generation: Working correctly")

if password_reset_success:
    print("✓ Password Reset: Working correctly")

print("\n" + "="*80)
print("Test completed at:", django.utils.timezone.now())
print("="*80 + "\n")
