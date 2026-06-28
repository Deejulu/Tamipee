#!/bin/bash
set -euo pipefail

echo "--- start.sh diagnostics ---"
echo "PWD=$(pwd)"
echo "DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-<unset>}"

# Validate DATABASE_URL before proceeding
if [ -z "${DATABASE_URL:-}" ]; then
    echo "ERROR: DATABASE_URL environment variable is not set!"
    echo "Please set DATABASE_URL in your Render dashboard."
    exit 1
fi

# Check DATABASE_URL format for common Supabase issues
echo "Validating DATABASE_URL format..."
python - <<'PY'
import os
import sys
from urllib.parse import urlparse

db_url = os.getenv("DATABASE_URL", "")
if not db_url:
    print("ERROR: DATABASE_URL is empty")
    sys.exit(1)

try:
    parsed = urlparse(db_url)
    
    # Basic validation
    if parsed.scheme not in ["postgres", "postgresql"]:
        print(f"ERROR: Invalid DATABASE_URL scheme '{parsed.scheme}'. Expected 'postgresql' or 'postgres'.")
        sys.exit(1)
    
    if not parsed.hostname:
        print("ERROR: DATABASE_URL missing hostname")
        sys.exit(1)
    
    if not parsed.username:
        print("ERROR: DATABASE_URL missing username")
        sys.exit(1)
    
    if not parsed.password:
        print("ERROR: DATABASE_URL missing password")
        sys.exit(1)
    
    # Supabase-specific validation
    if "supabase.com" in parsed.hostname:
        if "pooler.supabase.com" in parsed.hostname:
            # Pooler format: postgres.[PROJECT_REF] as username
            if not parsed.username.startswith("postgres."):
                print(f"ERROR: Supabase pooler connection requires username format 'postgres.[PROJECT_REF]'")
                print(f"Current username: '{parsed.username}'")
                print("")
                print("CORRECT FORMAT (Pooler):")
                print("postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres")
                print("")
                print("OR use Direct Connection (recommended for Django):")
                print("postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres")
                sys.exit(1)
        elif ".supabase.co" in parsed.hostname:
            # Direct connection: just 'postgres' as username
            if parsed.username != "postgres":
                print(f"WARNING: Supabase direct connection typically uses 'postgres' as username")
                print(f"Current username: '{parsed.username}'")
    
    print(f"✓ DATABASE_URL validation passed")
    print(f"  Host: {parsed.hostname}")
    print(f"  Port: {parsed.port or 'default'}")
    print(f"  User: {parsed.username}")
    print(f"  Database: {parsed.path.lstrip('/')}")
    
except Exception as e:
    print(f"ERROR: Failed to parse DATABASE_URL: {e}")
    sys.exit(1)
PY

if [ $? -ne 0 ]; then
    echo "DATABASE_URL validation failed. Please fix the connection string in Render dashboard."
    exit 1
fi

# Rewrite DATABASE_URL to use an explicit IPv4 host so psycopg/libpq can't pick IPv6.
echo "Resolving DATABASE_URL host to IPv4..."
IPV4_DATABASE_URL="$(python - <<'PY'
import os
import socket
import sys
from urllib.parse import urlparse, urlunparse

db_url = os.getenv("DATABASE_URL", "")
parsed = urlparse(db_url)

if not parsed.hostname:
    print("ERROR: DATABASE_URL has no hostname", file=sys.stderr)
    sys.exit(2)

port = parsed.port or 5432

try:
    ipv4 = socket.getaddrinfo(
        parsed.hostname,
        port,
        socket.AF_INET,
        socket.SOCK_STREAM,
    )[0][4][0]
except socket.gaierror as exc:
    print(f"ERROR: Unable to resolve IPv4 for {parsed.hostname}: {exc}", file=sys.stderr)
    sys.exit(3)

userinfo = ""
if parsed.username is not None:
    userinfo = parsed.username
    if parsed.password is not None:
        userinfo += f":{parsed.password}"
    userinfo += "@"

netloc = f"{userinfo}{ipv4}:{port}"
rewritten = parsed._replace(netloc=netloc)

print(urlunparse(rewritten))
PY
)"

if [ -z "${IPV4_DATABASE_URL:-}" ]; then
    echo "ERROR: Failed to generate IPv4 DATABASE_URL"
    exit 1
fi

export DATABASE_URL="$IPV4_DATABASE_URL"

python - <<'PY'
import os
from urllib.parse import urlparse

parsed = urlparse(os.getenv("DATABASE_URL", ""))
print(f"✓ IPv4 DATABASE_URL prepared")
print(f"  Host(IP): {parsed.hostname}")
print(f"  Port: {parsed.port or 'default'}")
PY

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



