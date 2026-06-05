#!/bin/bash
python manage.py migrate
python manage.py create_superuser_from_env

# Use Gunicorn to serve the WSGI app.
gunicorn tamipee.wsgi:application --bind 0.0.0.0:$PORT
