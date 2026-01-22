#!/usr/bin/env python
"""
Simple SMTP Connectivity Test
Diagnoses SMTP connection and authentication issues
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stem_app.settings')
django.setup()

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

print("\n" + "="*80)
print("SIMPLE SMTP CONNECTIVITY TEST")
print("="*80 + "\n")

print("📋 SMTP Configuration:")
print("-" * 80)
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"EMAIL_HOST_PASSWORD: {'*' * 10} (masked)")
print()

# Test 1: DNS Resolution
print("🔍 Test 1: DNS Resolution")
print("-" * 80)
try:
    import socket
    ip = socket.gethostbyname(settings.EMAIL_HOST)
    print(f"✓ DNS resolved {settings.EMAIL_HOST} to {ip}")
except socket.gaierror as e:
    print(f"✗ DNS resolution failed: {e}")
    sys.exit(1)

# Test 2: Port connectivity
print("\n🔍 Test 2: Port Connectivity")
print("-" * 80)
try:
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((settings.EMAIL_HOST, settings.EMAIL_PORT))
    sock.close()
    if result == 0:
        print(f"✓ Port {settings.EMAIL_PORT} is open on {settings.EMAIL_HOST}")
    else:
        print(f"✗ Could not connect to {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
except Exception as e:
    print(f"✗ Connection test failed: {e}")

# Test 3: SMTP Connection
print("\n🔍 Test 3: SMTP Connection")
print("-" * 80)
try:
    print(f"Connecting to {settings.EMAIL_HOST}:{settings.EMAIL_PORT}...")
    smtp = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10)
    print(f"✓ SMTP connection established")
    print(f"  Server response: {smtp.ehlo()[1].decode() if smtp.ehlo()[1] else 'OK'}")
    smtp.quit()
except smtplib.SMTPServerDisconnected as e:
    print(f"✗ SMTP server disconnected: {e}")
except smtplib.SMTPException as e:
    print(f"✗ SMTP error: {e}")
except socket.timeout:
    print(f"✗ Connection timeout (5s) - server may be down or port blocked")
except Exception as e:
    print(f"✗ Connection error: {e}")

# Test 4: TLS
print("\n🔍 Test 4: TLS/STARTTLS")
print("-" * 80)
try:
    smtp = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10)
    print(f"✓ Connected to SMTP server")
    print(f"Starting TLS...")
    smtp.starttls()
    print(f"✓ TLS started successfully")
    smtp.quit()
except smtplib.SMTPNotSupportedError:
    print(f"✗ STARTTLS not supported")
except smtplib.SMTPException as e:
    print(f"✗ STARTTLS failed: {e}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 5: Authentication
print("\n🔍 Test 5: SMTP Authentication")
print("-" * 80)
try:
    smtp = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10)
    print(f"✓ Connected to SMTP server")
    
    if settings.EMAIL_USE_TLS:
        smtp.starttls()
        print(f"✓ TLS enabled")
    
    print(f"Authenticating as {settings.EMAIL_HOST_USER}...")
    smtp.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    print(f"✓ Authentication successful!")
    smtp.quit()
except smtplib.SMTPAuthenticationError as e:
    print(f"✗ Authentication failed: {e}")
    print(f"  Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in settings.py")
except smtplib.SMTPException as e:
    print(f"✗ SMTP error: {e}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 6: Send test email (without actually sending)
print("\n🔍 Test 6: Email Composition")
print("-" * 80)
try:
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'SMTP Test Email'
    msg['From'] = settings.DEFAULT_FROM_EMAIL
    msg['To'] = 'test@example.com'
    
    part1 = MIMEText('This is a plain text version', 'plain')
    part2 = MIMEText('<p>This is an HTML version</p>', 'html')
    
    msg.attach(part1)
    msg.attach(part2)
    
    print(f"✓ Email composed successfully")
    print(f"  From: {msg['From']}")
    print(f"  To: {msg['To']}")
    print(f"  Subject: {msg['Subject']}")
except Exception as e:
    print(f"✗ Error composing email: {e}")

# Test 7: Full send test (actual send with error handling)
print("\n🔍 Test 7: Full Send Test (DRY RUN)")
print("-" * 80)
print("⚠️  NOTE: This test will NOT actually send an email, just verify the connection")
print()

try:
    smtp = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10)
    
    if settings.EMAIL_USE_TLS:
        smtp.starttls()
    
    smtp.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    print(f"✓ Connection and authentication verified")
    print(f"✓ Ready to send emails!")
    
    # Verify command
    smtp.noop()
    print(f"✓ NOOP command successful (connection still active)")
    
    smtp.quit()
except Exception as e:
    print(f"✗ Send test failed: {e}")

print("\n" + "="*80)
print("SMTP DIAGNOSTICS COMPLETE")
print("="*80 + "\n")
