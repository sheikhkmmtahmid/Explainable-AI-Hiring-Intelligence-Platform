#!/bin/bash
set -e

export DJANGO_SETTINGS_MODULE=config.settings.huggingface

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Celery worker in background..."
celery -A config.celery worker --loglevel=warning --concurrency=2 &

echo "Starting Gunicorn on port 7860..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:7860 \
    --workers 2 \
    --timeout 120 \
    --log-level info
