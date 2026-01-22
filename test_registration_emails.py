#!/usr/bin/env python
"""
Test script to verify registration notification emails are sent correctly.
This script tests:
1. Learner welcome emails
2. Tutor application received emails
3. Tutor approval emails
4. Tutor rejection emails
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stem_app.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.contrib.auth import get_user_model
from main.models.tutor import TutorApplication
from main.utils.mail import (
    send_learner_welcome_email,
    send_tutor_application_received_email,
    send_tutor_approval_email,
    send_tutor_rejection_email,
)

User = get_user_model()


def test_learner_welcome_email():
    """Test sending welcome email to a learner."""
    print("\n" + "=" * 60)
    print("TEST 1: Sending Learner Welcome Email")
    print("=" * 60)
    
    # Create a test learner
    test_user = User.objects.create_user(
        username='test_learner_001',
        email='test_learner@example.com',
        password='testpass123',
        first_name='Test',
        last_name='Learner',
        display_name='Test Learner'
    )
    
    print(f"✓ Created test learner: {test_user.username} ({test_user.email})")
    
    # Send welcome email
    result = send_learner_welcome_email(test_user)
    print(f"✓ Welcome email sent: {result}")
    print(f"  Email Backend: {settings.EMAIL_BACKEND}")
    
    # Cleanup
    test_user.delete()
    print("✓ Test user cleaned up\n")
    return result


def test_tutor_application_received_email():
    """Test sending tutor application received confirmation email."""
    print("=" * 60)
    print("TEST 2: Sending Tutor Application Received Email")
    print("=" * 60)
    
    # Create a test tutor
    test_tutor = User.objects.create_user(
        username='test_tutor_001',
        email='test_tutor@example.com',
        password='testpass123',
        first_name='Test',
        last_name='Tutor',
        display_name='Test Tutor',
        is_tutor=False,
        is_active=False
    )
    
    print(f"✓ Created test tutor: {test_tutor.username} ({test_tutor.email})")
    
    # Send application received email
    result = send_tutor_application_received_email(test_tutor)
    print(f"✓ Application received email sent: {result}")
    print(f"  Email Backend: {settings.EMAIL_BACKEND}")
    
    # Cleanup
    test_tutor.delete()
    print("✓ Test user cleaned up\n")
    return result


def test_tutor_approval_email():
    """Test sending tutor approval email."""
    print("=" * 60)
    print("TEST 3: Sending Tutor Approval Email")
    print("=" * 60)
    
    # Create a test tutor
    test_tutor = User.objects.create_user(
        username='test_tutor_002',
        email='test_tutor_approval@example.com',
        password='testpass123',
        first_name='Test',
        last_name='Tutor Approved',
        display_name='Test Tutor Approved',
        is_tutor=False,
        is_active=False
    )
    
    print(f"✓ Created test tutor: {test_tutor.username} ({test_tutor.email})")
    
    # Send approval email
    result = send_tutor_approval_email(test_tutor)
    print(f"✓ Approval email sent: {result}")
    print(f"  Email Backend: {settings.EMAIL_BACKEND}")
    
    # Cleanup
    test_tutor.delete()
    print("✓ Test user cleaned up\n")
    return result


def test_tutor_rejection_email():
    """Test sending tutor rejection email with notes."""
    print("=" * 60)
    print("TEST 4: Sending Tutor Rejection Email")
    print("=" * 60)
    
    # Create a test tutor
    test_tutor = User.objects.create_user(
        username='test_tutor_003',
        email='test_tutor_rejection@example.com',
        password='testpass123',
        first_name='Test',
        last_name='Tutor Rejected',
        display_name='Test Tutor Rejected',
        is_tutor=False,
        is_active=False
    )
    
    print(f"✓ Created test tutor: {test_tutor.username} ({test_tutor.email})")
    
    # Send rejection email with notes
    rejection_notes = "Qualifications do not meet minimum requirements. Please reapply with additional certifications."
    result = send_tutor_rejection_email(test_tutor, notes=rejection_notes)
    print(f"✓ Rejection email sent: {result}")
    print(f"  Rejection Notes: {rejection_notes}")
    print(f"  Email Backend: {settings.EMAIL_BACKEND}")
    
    # Cleanup
    test_tutor.delete()
    print("✓ Test user cleaned up\n")
    return result


def print_email_config():
    """Print current email configuration."""
    print("\n" + "=" * 60)
    print("CURRENT EMAIL CONFIGURATION")
    print("=" * 60)
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    if 'console' in settings.EMAIL_BACKEND.lower():
        print("\n⚠️  WARNING: Using CONSOLE email backend!")
        print("   Emails are printed to console, not sent via SMTP.")
        print("   To enable SMTP, change EMAIL_BACKEND to:")
        print("   'django.core.mail.backends.smtp.EmailBackend'")
    else:
        print("\n✓ Using SMTP email backend (emails will be sent)")
    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("REGISTRATION EMAIL NOTIFICATION TESTS")
    print("=" * 60)
    
    # Print email configuration
    print_email_config()
    
    # Run tests
    results = {
        'Learner Welcome Email': test_learner_welcome_email(),
        'Tutor Application Received Email': test_tutor_application_received_email(),
        'Tutor Approval Email': test_tutor_approval_email(),
        'Tutor Rejection Email': test_tutor_rejection_email(),
    }
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
    else:
        print("✗ SOME TESTS FAILED!")
    print("=" * 60 + "\n")
    
    return all_passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
