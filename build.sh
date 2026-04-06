#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
mkdir -p /app/data
python manage.py migrate
python manage.py collectstatic --no-input
