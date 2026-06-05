"""
WSGI config for tamipee project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tamipee.settings')


def create_superuser_from_env():
    username = os.getenv('DJANGO_SUPERUSER_USERNAME', '').strip()
    password = os.getenv('DJANGO_SUPERUSER_PASSWORD', '').strip()
    email = os.getenv('DJANGO_SUPERUSER_EMAIL', '').strip()

    if not username or not password:
        return

    if not email:
        email = f'{username}@example.com'

    UserModel = get_user_model()
    try:
        user = UserModel.objects.filter(username=username).first()
        if user:
            user.email = email
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
            if hasattr(user, 'role'):
                user.role = 'admin'
            user.set_password(password)
            user.save(update_fields=['password', 'email', 'is_active', 'is_staff', 'is_superuser', 'role'])
            print(f'Updated existing user to superuser credentials: {username}')
            return

        UserModel.objects.create_superuser(username=username, email=email, password=password)
        print(f'Created superuser: {username}')
    except Exception as exc:
        print(f'Failed to create or update superuser {username}:', exc, file=sys.stderr)


try:
    call_command('migrate', interactive=False)
    create_superuser_from_env()
except Exception as exc:
    print('Startup initialization failed:', exc, file=sys.stderr)

application = get_wsgi_application()
