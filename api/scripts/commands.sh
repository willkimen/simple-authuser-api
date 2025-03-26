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
# 4. Starts Django in using Gunicorn.
#
# Environment Variables:
# - POSTGRES_HOST: Hostname of the PostgreSQL database.
# - POSTGRES_PORT: Port of the PostgreSQL database.
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
python manage.py schedule_delete_expired_accounts
python manage.py schedule_notify_expired_account_deletion

touch /home/djuser/my_environment
echo "MIGRATED=True" >> /home/djuser/my_environment
echo "MIGRATED environment variable set to True"

echo "Starting Gunicorn..."
gunicorn --bind 0.0.0.0:8000 config.wsgi

