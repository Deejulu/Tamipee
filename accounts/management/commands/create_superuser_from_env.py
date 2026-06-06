import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create or update a superuser from DJANGO_SUPERUSER_* environment variables.'

    def handle(self, *args, **options):
        username = os.getenv('DJANGO_SUPERUSER_USERNAME', '').strip()
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD', '').strip()
        email = os.getenv('DJANGO_SUPERUSER_EMAIL', '').strip()

        # Fallback: keep deploy reproducible without requiring Render env vars.
        # Uses the requested default superuser credentials.
        if not username or not password:
            username = 'iamadmin'
            password = 'david0011'
            if not email:
                email = f'{username}@example.com'
            self.stdout.write(self.style.WARNING(
                'DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD were not set. '
                'Using fallback credentials for "iamadmin".'
            ))

        if not email:
            email = f'{username}@example.com'

        UserModel = get_user_model()
        user = UserModel.objects.filter(username=username).first()

        if user:
            user.email = email
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
            user.set_password(password)
            user.save(update_fields=['email', 'is_active', 'is_staff', 'is_superuser', 'password'])
            self.stdout.write(self.style.SUCCESS(
                f'Updated existing user "{username}" to superuser and set password.'
            ))
            return

        UserModel.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f'Created superuser "{username}".'))
