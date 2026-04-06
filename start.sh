#!/usr/bin/env bash
set -o errexit

python manage.py migrate

python manage.py shell -c "
from django.contrib.auth import get_user_model
import os

User = get_user_model()

username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if username and email and password:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={'email': email}
    )
    user.email = email
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)
    user.save()
    print(f'Admin ready: {username} | created={created}')
else:
    print('Admin env vars not fully set; skipping admin bootstrap')
"

exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8080}