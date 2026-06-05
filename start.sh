#!/bin/bash
python manage.py migrate
gunicorn tamipee.wsgi:application --bind 0.0.0.0:$PORT
