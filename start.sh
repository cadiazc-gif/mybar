#!/usr/bin/env bash
set -o errexit

mkdir -p /app/data
touch /app/data/db.sqlite3
python manage.py migrate
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8080}