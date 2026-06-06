"""
WSGI config for tamipee project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys
import traceback
import uuid

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tamipee.settings')


def create_superuser_from_env():
    username = os.getenv('DJANGO_SUPERUSER_USERNAME', '').strip()
    password = os.getenv('DJANGO_SUPERUSER_PASSWORD', '').strip()
    email = os.getenv('DJANGO_SUPERUSER_EMAIL', '').strip()

    print('WSGI startup: superuser env check', file=sys.stdout)
    print(f'  DJANGO_SUPERUSER_USERNAME={username!r}', file=sys.stdout)
    print(f'  DJANGO_SUPERUSER_PASSWORD_set={bool(password)}', file=sys.stdout)
    print(f'  DJANGO_SUPERUSER_EMAIL={email!r}', file=sys.stdout)
    sys.stdout.flush()

    if not username or not password:
        print('Skipping superuser creation: username or password missing.', file=sys.stdout)
        sys.stdout.flush()
        return

    if not email:
        email = f'{username}+{uuid.uuid4().hex[:8]}@example.com'

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
            update_fields = ['password', 'email', 'is_active', 'is_staff', 'is_superuser']
            if hasattr(user, 'role'):
                update_fields.append('role')
            user.save(update_fields=update_fields)
            print(f'Updated existing user to superuser credentials: {username}', file=sys.stdout)
            sys.stdout.flush()
            return

        UserModel.objects.create_superuser(username=username, email=email, password=password)
        print(f'Created superuser: {username}', file=sys.stdout)
        sys.stdout.flush()
    except Exception:
        print(f'Failed to create or update superuser {username}:', file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()


# NOTE:
# Do NOT run migrations or superuser creation in WSGI import.
# Render will run these during start/release (see start.sh / render.yaml).
application = get_wsgi_application()
