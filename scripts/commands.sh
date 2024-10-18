#!/bin/sh

set -e

while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  echo "🟡 Waiting for Postgres Database Startup ($POSTGRES_HOST $POSTGRES_PORT) ..."
  sleep 2
done

echo "✅ Postgres Database Started Successfully ($POSTGRES_HOST:$POSTGRES_PORT)"

echo "Applying migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

if [ "$DJANGO_ENV" = "production" ]; then
    echo "Starting Gunicorn for production..."
    gunicorn --bind 0.0.0.0:8000 config.wsgi
elif [ "$DJANGO_ENV" = "development" ]; then
    echo "Starting Django development server..."
    python manage.py runserver 0.0.0.0:8000
else
    echo "Unknown environment: $DJANGO_ENV"
    echo "Please set DJANGO_ENV to either 'development' or 'production'."
    exit 1
fi

