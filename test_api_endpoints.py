#!/usr/bin/env python
"""
API ENDPOINT TESTING - Forgot Password & Reset Password
Tests the actual API endpoints using curl commands
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stem_app.settings')
django.setup()

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from main.models import CustomUser

print("\n")
print("=" * 80)
print("API ENDPOINT TESTING - FORGOT PASSWORD & RESET PASSWORD")
print("=" * 80)
print()

# Get test user
test_user = CustomUser.objects.filter(email="testuser@stemapp.local").first()
if not test_user:
    print("✗ Test user not found. Creating...")
    test_user = CustomUser.objects.create_user(
        username="testuser_smtp",
        email="testuser@stemapp.local",
        password="TestPassword123!@#"
    )
    print(f"✓ Created test user: {test_user.username}")

print()
print("Test User Info:")
print(f"  Username: {test_user.username}")
print(f"  Email: {test_user.email}")
print(f"  User ID: {test_user.id}")
print()

# ============================================================================
# ENDPOINT 1: Forgot Password (GET)
# ============================================================================
print("-" * 80)
print("ENDPOINT 1: Forgot Password Form (GET)")
print("-" * 80)
print()
print("Request:")
print("  Method: GET")
print("  URL: http://localhost:8000/forgot-password/")
print()
print("cURL Command:")
print('  curl -X GET "http://localhost:8000/forgot-password/"')
print()
print("Expected Response:")
print("  - HTML form with email/username input field")
print("  - 200 OK status")
print()

# ============================================================================
# ENDPOINT 2: Send Forgot Password Email (POST)
# ============================================================================
print("-" * 80)
print("ENDPOINT 2: Send Forgot Password Email (POST)")
print("-" * 80)
print()
print("Request:")
print("  Method: POST")
print("  URL: http://localhost:8000/api/auth/forgot-password/")
print("  Content-Type: application/json")
print()
print("Request Body (JSON):")
print("  Option A - By email:")
print('    {"email": "testuser@stemapp.local"}')
print()
print("  Option B - By username:")
print('    {"username": "testuser_smtp"}')
print()
print("cURL Command (Email):")
print('  curl -X POST "http://localhost:8000/api/auth/forgot-password/" \\')
print('    -H "Content-Type: application/json" \\')
print('    -d \'{"email": "testuser@stemapp.local"}\'')
print()
print("cURL Command (Username):")
print('  curl -X POST "http://localhost:8000/api/auth/forgot-password/" \\')
print('    -H "Content-Type: application/json" \\')
print('    -d \'{"username": "testuser_smtp"}\'')
print()
print("Expected Response:")
print('  {"success": true, "message": "Email sent successfully"}')
print("  - 200 OK status")
print("  - Check Django dev server console for email output")
print()

# ============================================================================
# ENDPOINT 3: Reset Password Form (GET)
# ============================================================================
print("-" * 80)
print("ENDPOINT 3: Reset Password Form (GET)")
print("-" * 80)
print()

# Generate token for demo
token = default_token_generator.make_token(test_user)
uid = urlsafe_base64_encode(force_bytes(test_user.pk))

print("Request:")
print("  Method: GET")
print("  URL: http://localhost:8000/reset-password/<uid>/<token>/")
print()
print(f"Example URL (for user {test_user.username}):")
print(f"  http://localhost:8000/reset-password/{uid}/{token}/")
print()
print("cURL Command:")
print(f'  curl -X GET "http://localhost:8000/reset-password/{uid}/{token}/"')
print()
print("Expected Response:")
print("  - HTML form with new password input fields")
print("  - 200 OK status")
print("  - Form hidden inputs with uid and token")
print()

# ============================================================================
# ENDPOINT 4: Reset Password (POST)
# ============================================================================
print("-" * 80)
print("ENDPOINT 4: Reset Password (POST)")
print("-" * 80)
print()
print("Request:")
print("  Method: POST")
print("  URL: http://localhost:8000/api/auth/reset-password/")
print("  Content-Type: application/json")
print()
print("Request Body (JSON):")
print(f'  {{"uid": "{uid}", "token": "{token}", "new_password": "NewPassword123!@#", "confirm_password": "NewPassword123!@#"}}')
print()
print("cURL Command:")
print('  curl -X POST "http://localhost:8000/api/auth/reset-password/" \\')
print('    -H "Content-Type: application/json" \\')
print(f'    -d \'{{"uid": "{uid}", "token": "{token}", "new_password": "NewPassword123!@#", "confirm_password": "NewPassword123!@#"}}\'')
print()
print("Expected Response:")
print('  {"success": true, "message": "Password reset successfully"}')
print("  - 200 OK status")
print()

# ============================================================================
# COMPLETE TESTING FLOW
# ============================================================================
print("-" * 80)
print("COMPLETE TESTING FLOW (Manual Steps)")
print("-" * 80)
print()
print("Step 1: Start Django development server")
print("  $ python manage.py runserver")
print()
print("Step 2: Open web browser to forgot password page")
print("  URL: http://localhost:8000/forgot-password/")
print()
print("Step 3: Enter email or username in the form")
print("  Email: testuser@stemapp.local")
print("  (or Username: testuser_smtp)")
print()
print("Step 4: Submit the form")
print("  - Look in Django console for email output")
print("  - Copy the reset-password link from the console output")
print()
print("Step 5: Navigate to the reset password link")
print("  Example: http://localhost:8000/reset-password/MjE/d2t99y.../")
print()
print("Step 6: Enter new password and confirm")
print("  - Both passwords must match")
print("  - Password should be strong (min 8 chars recommended)")
print()
print("Step 7: Submit the form")
print("  - Should see success message")
print("  - Try logging in with new password")
print()

# ============================================================================
# API RESPONSE EXAMPLES
# ============================================================================
print("-" * 80)
print("API RESPONSE EXAMPLES")
print("-" * 80)
print()

print("Success Response (Forgot Password):")
print("""
{
  "success": true,
  "message": "Email sent successfully. Check your inbox for password reset link."
}
""")

print("Success Response (Reset Password):")
print("""
{
  "success": true,
  "message": "Password reset successfully. You can now login with your new password."
}
""")

print("Error Response (Invalid Email):")
print("""
{
  "success": false,
  "message": "Email or username not found"
}
""")

print("Error Response (Invalid Token):")
print("""
{
  "success": false,
  "message": "Invalid or expired reset link. Please try again."
}
""")

# ============================================================================
# TROUBLESHOOTING
# ============================================================================
print("-" * 80)
print("TROUBLESHOOTING")
print("-" * 80)
print()

print("Issue: Email not appearing in console")
print("  Solution:")
print("    1. Check settings.py EMAIL_BACKEND is set to console")
print("    2. Make sure Django dev server is running in the right terminal")
print("    3. Try hitting the endpoint again")
print()

print("Issue: Invalid token when accessing reset link")
print("  Solution:")
print("    1. Token expires after 24 hours - request a new one")
print("    2. Check UID and token are properly encoded in URL")
print("    3. Make sure user hasn't been modified since token generation")
print()

print("Issue: 404 error on endpoints")
print("  Solution:")
print("    1. Check main/urls.py has the endpoints defined")
print("    2. Verify paths match exactly (with trailing slashes)")
print("    3. Check stem_app/urls.py includes main app URLs")
print()

print("Issue: Password reset succeeds but can't login")
print("  Solution:")
print("    1. Verify new password was entered correctly (twice)")
print("    2. Check password contains no typos (case-sensitive)")
print("    3. Try resetting password again")
print()

print("=" * 80)
print("Testing guide complete!")
print("=" * 80)
print()
