#!/usr/bin/env python
"""
Advanced SMTP Diagnostics - Determine if password is wrong or network blocked
"""

import smtplib
import socket
import ssl

print("\n" + "="*80)
print("ADVANCED SMTP DIAGNOSTICS")
print("="*80 + "\n")

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = 'stemappza@gmail.com'
EMAIL_PASSWORD = 'ddtz gltz vscj loab'

print("Configuration:")
print(f"  Host: {EMAIL_HOST}")
print(f"  Port: {EMAIL_PORT}")
print(f"  User: {EMAIL_USER}")
print(f"  Password: {'*' * len(EMAIL_PASSWORD)}")
print()

# Test 1: Raw Socket Connection
print("=" * 80)
print("TEST 1: Raw Socket Connection (Can we reach the server?)")
print("=" * 80)
try:
    print(f"Attempting socket connection to {EMAIL_HOST}:{EMAIL_PORT}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((EMAIL_HOST, EMAIL_PORT))
    sock.close()
    
    if result == 0:
        print(f"✓ Socket connection successful!")
    else:
        print(f"✗ Socket connection failed: Error {result}")
        print("  This means the network cannot reach the SMTP server")
except Exception as e:
    print(f"✗ Socket error: {e}")

print()

# Test 2: SMTP Connection without TLS
print("=" * 80)
print("TEST 2: SMTP Connection (without TLS first)")
print("=" * 80)
try:
    print(f"Connecting to SMTP server...")
    smtp = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
    print(f"✓ SMTP connection established!")
    print(f"  Server greeted with: {smtp.getwelcome()}")
    smtp.quit()
except socket.timeout:
    print(f"✗ Connection timeout (10s)")
    print("  Network is blocking or server is not responding")
except ConnectionRefusedError:
    print(f"✗ Connection refused")
    print("  Server refused connection (wrong port?)")
except Exception as e:
    print(f"✗ SMTP connection error: {e}")

print()

# Test 3: SMTP with TLS
print("=" * 80)
print("TEST 3: SMTP Connection with STARTTLS")
print("=" * 80)
try:
    print(f"Connecting to SMTP server...")
    smtp = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
    print(f"✓ SMTP connection established")
    
    print(f"Starting TLS...")
    smtp.starttls()
    print(f"✓ TLS negotiation successful")
    
    smtp.quit()
except socket.timeout:
    print(f"✗ Timeout during connection/TLS")
    print("  Network is blocking or server is slow")
except smtplib.SMTPNotSupportedError:
    print(f"✗ STARTTLS not supported")
except Exception as e:
    print(f"✗ TLS error: {e}")

print()

# Test 4: Full Authentication
print("=" * 80)
print("TEST 4: Full Authentication Test")
print("=" * 80)
try:
    print(f"Connecting to SMTP server...")
    smtp = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
    print(f"✓ Connected")
    
    print(f"Starting TLS...")
    smtp.starttls()
    print(f"✓ TLS started")
    
    print(f"Attempting login as {EMAIL_USER}...")
    smtp.login(EMAIL_USER, EMAIL_PASSWORD)
    print(f"✓ Authentication SUCCESSFUL!")
    print(f"  Your password is CORRECT")
    
    # Try sending test email
    print()
    print("Attempting to send test email...")
    smtp.sendmail(
        EMAIL_USER,
        'bjmbalaka@gmail.com',
        '''From: STEM LMS <stemappza@gmail.com>
To: bjmbalaka@gmail.com
Subject: STEM LMS - Test Email

If you receive this, SMTP is working!

Status: Email sent successfully from Django
'''
    )
    print(f"✓ Email sent successfully!")
    
    smtp.quit()
    
except smtplib.SMTPAuthenticationError as e:
    print(f"✗ Authentication FAILED")
    print(f"  Error: {e}")
    print(f"  Your password is WRONG or:")
    print(f"    - Google account security blocked the login")
    print(f"    - App Password is invalid")
    print(f"    - Credentials are case-sensitive")
    
except socket.timeout:
    print(f"✗ Timeout (network is blocking)")
    print(f"  This is NOT a password issue")
    print(f"  Your network/firewall is blocking SMTP port 587")
    
except smtplib.SMTPException as e:
    print(f"✗ SMTP error: {e}")
    
except Exception as e:
    print(f"✗ Error: {e}")

print()
print("=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80 + "\n")

# Summary
print("INTERPRETATION:")
print("-" * 80)
print()
print("If you see '✓ Authentication SUCCESSFUL':")
print("  → Your password is CORRECT")
print("  → SMTP is working")
print()
print("If you see '✗ Authentication FAILED' + 'Invalid credentials':")
print("  → Your password is WRONG")
print("  → Fix: Update EMAIL_HOST_PASSWORD in settings.py")
print()
print("If you see '✗ Timeout' or 'Connection refused':")
print("  → Network/firewall is blocking SMTP")
print("  → Password is irrelevant (can't reach server)")
print("  → This is expected in development environment")
print()
