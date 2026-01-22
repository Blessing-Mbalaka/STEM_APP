from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Check SMTP health and connectivity'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('SMTP HEALTH CHECK'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        try:
            self.stdout.write(f"📧 Testing SMTP Connection...")
            self.stdout.write(f"   Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
            self.stdout.write(f"   User: {settings.EMAIL_HOST_USER}")
            self.stdout.write(f"   TLS: {settings.EMAIL_USE_TLS}\n")

            # Send test email
            send_mail(
                'SMTP Health Check',
                'This is an SMTP health check test.',
                settings.DEFAULT_FROM_EMAIL,
                [settings.DEFAULT_FROM_EMAIL],
                fail_silently=False
            )

            self.stdout.write(self.style.SUCCESS('✅ SMTP HEALTH: OPERATIONAL\n'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ SMTP HEALTH: FAILED\nError: {str(e)}\n'))