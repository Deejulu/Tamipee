"""
WSGI config for tamipee project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys

from django.core.management import call_command
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tamipee.settings')

try:
    call_command('migrate', interactive=False)
except Exception as exc:
    print('Auto-migrate failed:', exc, file=sys.stderr)

application = get_wsgi_application()
