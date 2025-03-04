#!/bin/sh

# -----------------------------------------------------------------------------
# Django Container Startup Script
#
# This script ensures that the PostgreSQL database is ready before applying
# migrations and starting the Django application.
#
# Functionality:
# 1. Waits for PostgreSQL to be available before proceeding.
# 2. Applies Django database migrations.
# 3. Creates a flag file to indicate that migrations have been executed.
# 4. Starts Django in production mode using Gunicorn or in development mode
#    using the built-in Django server, based on the API_ENV environment variable.
#
# Environment Variables:
# - POSTGRES_HOST: Hostname of the PostgreSQL database.
# - POSTGRES_PORT: Port of the PostgreSQL database.
# - API_ENV: Determines whether to run the app in "production" or "development".
# -----------------------------------------------------------------------------
set -e

while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  echo "🟡 Waiting for Postgres Database Startup ($POSTGRES_HOST $POSTGRES_PORT) ..."
  sleep 2
done

echo "✅ Postgres Database Started Successfully ($POSTGRES_HOST:$POSTGRES_PORT)"

echo "Applying migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

python manage.py schedule_expired_codes_removal
python manage.py schedule_expired_tokens_removal
python manage.py schedule_notify_first_reminder
python manage.py schedule_notify_second_reminder

touch /home/djuser/my_environment
echo "MIGRATED=True" >> /home/djuser/my_environment
echo "MIGRATED environment variable set to True"

if [ "$API_ENV" = "production" ]; then
    echo "Starting Gunicorn for production..."
    gunicorn --bind 0.0.0.0:8000 config.wsgi
elif [ "$API_ENV" = "development" ]; then
    echo "Starting Django development server..."
    python manage.py runserver 0.0.0.0:8000
else
    echo "Unknown environment: $API_ENV"
    echo "Please set API_ENV to either 'development' or 'production'."
    exit 1
fi

