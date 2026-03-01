# Email Configuration Reference

This document provides a complete reference for your email settings that are currently working.

## Current Working Configuration

### settings.py Email Configuration

Located in `stem_app/settings.py` (lines 223-229):

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'stemappza@gmail.com'
EMAIL_HOST_PASSWORD = 'ddtz gltz vscj loab'  # App password for Gmail
DEFAULT_FROM_EMAIL = 'STEM LMS <stemappza@gmail.com>'
```

**Current Status**: ✅ Working with hardcoded credentials

---

## Recommended: Using Environment Variables (.env)

### .env File Template

Create a `.env` file in the root directory of your project with the following variables:

```
# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=stemappza@gmail.com
EMAIL_HOST_PASSWORD=ddtz gltz vscj loab
DEFAULT_FROM_EMAIL=STEM LMS <stemappza@gmail.com>
```

### Updated settings.py Configuration

To use environment variables instead of hardcoded credentials, replace the email configuration section with:

```python
# Email Configuration
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', f'STEM LMS <{EMAIL_HOST_USER}>')
```

---

## Settings Explanation

| Setting | Value | Purpose |
|---------|-------|---------|
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` | Uses SMTP to send emails |
| `EMAIL_HOST` | `smtp.gmail.com` | Gmail's SMTP server |
| `EMAIL_PORT` | `587` | SMTP port for TLS connections |
| `EMAIL_USE_TLS` | `True` | Enable Transport Layer Security |
| `EMAIL_USE_SSL` | `False` | Disable SSL (using TLS instead) |
| `EMAIL_HOST_USER` | `stemappza@gmail.com` | Gmail account address |
| `EMAIL_HOST_PASSWORD` | `ddtz gltz vscj loab` | Gmail App Password (not regular password) |
| `DEFAULT_FROM_EMAIL` | `STEM LMS <stemappza@gmail.com>` | Default sender name and email |

---

## Important Notes

### Gmail App Password
- The password `ddtz gltz vscj loab` is a **Gmail App Password**, not your regular Gmail password
- This is generated from Google Account settings → Security → App passwords
- More secure than using your actual Gmail password

### Port & TLS Configuration
- Port 587 is the standard for TLS connections (StartTLS)
- Port 465 is for SSL connections
- Current setup uses TLS (PORT 587, EMAIL_USE_TLS=True, EMAIL_USE_SSL=False)

### For Production Deployment
- **Never commit the .env file to version control** - add it to `.gitignore`
- Set environment variables on your hosting platform (Render, Heroku, AWS, etc.)
- The code will first check environment variables before using defaults

---

## Testing Your Configuration

Use the existing test scripts to verify the email setup:
```bash
python send_test_email.py
python test_smtp_simple.py
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Authentication failed | Verify the Gmail App Password is correct |
| Connection refused | Check that EMAIL_HOST and EMAIL_PORT are correct |
| Email not sent but no error | Ensure DEFAULT_FROM_EMAIL is set |

---

## Alternative Email Providers

If you want to use a different email provider:

```python
# SendGrid
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')

# AWS SES
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_REGION_NAME = 'us-east-1'

# Outlook/Office365
EMAIL_HOST = 'smtp.office365.com'
EMAIL_PORT = 587
```

---

**Last Updated**: March 1, 2026
**Status**: ✅ Verified and Working
