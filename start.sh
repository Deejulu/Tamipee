#!/bin/bash
set -euo pipefail

echo "--- start.sh diagnostics ---"
echo "PWD=$(pwd)"
echo "DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-<unset>}"

python -c "import os; from django.conf import settings; import pathlib; print('DJANGO_SETTINGS_MODULE from env=', os.getenv('DJANGO_SETTINGS_MODULE')); print('STATIC_ROOT=', settings.STATIC_ROOT); print('STATIC_ROOT exists before collectstatic:', pathlib.Path(settings.STATIC_ROOT).exists())" || true


# Collect static so WhiteNoise can serve STATIC_ROOT correctly on Render.
echo "Collecting static..."
python manage.py collectstatic --noinput --clear --verbosity 2

# Verify STATIC_ROOT exists and is not empty
echo "Verifying STATIC_ROOT..."
python -c "import pathlib; from django.conf import settings; p=pathlib.Path(settings.STATIC_ROOT); files=list(p.glob('**/*')); assert p.exists(), f'STATIC_ROOT missing after collectstatic: {p}'; assert files, f'STATIC_ROOT empty after collectstatic: {p}'; print(f'✓ STATIC_ROOT ready: {p} ({len(files)} items)')" || (echo "ERROR: Static files collection failed" && exit 1)

python manage.py migrate
python manage.py create_superuser_from_env
python manage.py seed_security_questions


python -c "import pathlib; from django.conf import settings; p=pathlib.Path(settings.STATIC_ROOT); print('STATIC_ROOT exists after all setup:', p.exists()); print('STATIC_ROOT=', settings.STATIC_ROOT); print('STATIC_ROOT listing (head):', list(p.glob('**/*'))[:10] if p.exists() else 'MISSING')" || true

# Use Gunicorn to serve the WSGI app.
echo "Starting gunicorn..."
gunicorn tamipee.wsgi:application --bind 0.0.0.0:$PORT
