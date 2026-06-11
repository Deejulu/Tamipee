#!/bin/bash
set -euo pipefail

echo "--- start.sh diagnostics ---"
echo "PWD=$(pwd)"
echo "DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-<unset>}"

python -c "import os; from django.conf import settings; import pathlib; print('DJANGO_SETTINGS_MODULE from env=', os.getenv('DJANGO_SETTINGS_MODULE')); print('STATIC_ROOT=', settings.STATIC_ROOT); print('STATIC_ROOT exists before collectstatic:', pathlib.Path(settings.STATIC_ROOT).exists())" || true

echo "--- start.sh filesystem diagnostics (before collectstatic) ---"
python - <<'PY'
import os
from django.conf import settings
from pathlib import Path
p = Path(settings.STATIC_ROOT)
print('CWD=', os.getcwd())
print('STATIC_ROOT=', p)
print('STATIC_ROOT exists=', p.exists())
if p.exists():
    print('STATIC_ROOT head items=', [x.name for x in p.glob('**/*')][:10])
PY

# Collect static so WhiteNoise can serve STATIC_ROOT correctly on Render.
echo "Collecting static..."
python manage.py collectstatic --noinput --clear --verbosity 2

echo "--- start.sh filesystem diagnostics (after collectstatic) ---"
python - <<'PY'
from django.conf import settings
from pathlib import Path
p = Path(settings.STATIC_ROOT)
print('STATIC_ROOT=', p)
print('STATIC_ROOT exists=', p.exists())
if p.exists():
    files = list(p.glob('**/*'))
    print('STATIC_ROOT items count=', len(files))
    print('STATIC_ROOT first files=', [str(x.relative_to(p)) for x in files[:10]])
    # ensure css exists
    css = p / 'css' / 'main.css'
    print('Expected CSS exists (staticfiles/css/main.css)=', css.exists())
else:
    print('STATIC_ROOT missing after collectstatic')
PY

# Create STATIC_ROOT directory explicitly so WhiteNoise doesn't warn even if collectstatic is a no-op.
python -c "import pathlib; from django.conf import settings; p=pathlib.Path(settings.STATIC_ROOT); p.mkdir(parents=True, exist_ok=True); print('Ensured STATIC_ROOT exists:', p)" || true


python manage.py migrate
python manage.py create_superuser_from_env
python manage.py seed_security_questions

# Post checks before starting the server
python -c "import pathlib; from django.conf import settings; p=pathlib.Path(settings.STATIC_ROOT); print('STATIC_ROOT exists after collectstatic/migrations:', p.exists()); print('STATIC_ROOT=', settings.STATIC_ROOT); print('STATIC_ROOT listing (head):', list(p.glob('**/*'))[:10] if p.exists() else 'MISSING')" || true

# Use Gunicorn to serve the WSGI app.
echo "Starting gunicorn..."
gunicorn tamipee.wsgi:application --bind 0.0.0.0:$PORT



