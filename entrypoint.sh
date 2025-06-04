#!/bin/bash

echo "Waiting for MySQL..."

until mysqladmin ping -h "db" --silent; do
  sleep 1
done

echo "MySQL started"

python manage.py collectstatic --noinput
python manage.py migrate --noinput

gunicorn substring_back.wsgi:application --bind 0.0.0.0:8000