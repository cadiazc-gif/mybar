#!/usr/bin/env bash
set -o errexit

mkdir -p /app/data
touch /app/data/db.sqlite3
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --no-input
