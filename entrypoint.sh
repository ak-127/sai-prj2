#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."

while ! nc -z postgres 5432; do
  sleep 1
done

echo "PostgreSQL is ready!"

echo "Applying migrations..."
python manage.py migrate --noinput

python manage.py createsuperuser --noinput || true

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Starting server..."

exec "$@"