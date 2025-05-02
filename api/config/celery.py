"""
Celery configuration module for Django.

This module configures and initializes an instance of Celery for the Django project.
It sets up distinct queues for specific tasks and enables task auto-discovery 
across Django apps. The settings are loaded from Django's configuration.

Functionality:
- Initializes the Celery instance with the Django project.
- Loads Celery settings from Django's settings.py.
- Defines task-specific queues for better task management.
- Enables automatic task discovery in Django apps.

Queues:
- EMAIL_QUEUE_NAME: Queue for email-related tasks. 
- REMOVALS_QUEUE_NAME: Queue for removal-related tasks.
"""

import os

from celery import Celery
from user_app.constants.celery import EMAIL_QUEUE_NAME, REMOVALS_QUEUE_NAME

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.task_routes = {
    "user_app.tasks.task_remove_exp_code": {"queue": REMOVALS_QUEUE_NAME},
    "user_app.tasks.task_remove_exp_token": {"queue": REMOVALS_QUEUE_NAME},
    "user_app.tasks.task_send_account_activation_code": {"queue": EMAIL_QUEUE_NAME},
    "user_app.tasks.task_send_email_change_code": {"queue": EMAIL_QUEUE_NAME},
    "user_app.tasks.task_send_reset_password_code": {"queue": EMAIL_QUEUE_NAME},
    "user_app.tasks.task_notify_activated_account": {"queue": EMAIL_QUEUE_NAME},
    "user_app.tasks.task_notify_changed_email": {"queue": EMAIL_QUEUE_NAME},
    "user_app.tasks.task_notify_reset_password": {"queue": EMAIL_QUEUE_NAME},
    "user_app.tasks.task_notify_deleted_account": {"queue": EMAIL_QUEUE_NAME},
    "user_app.tasks.task_notify_expired_account_deletion": {"queue": EMAIL_QUEUE_NAME},
    "user_app.tasks.task_notify_first_reminder": {"queue": EMAIL_QUEUE_NAME},
    "user_app.tasks.task_notify_second_reminder": {"queue": EMAIL_QUEUE_NAME},
    "user_app.tasks.task_delete_expired_accounts": {"queue": REMOVALS_QUEUE_NAME},
    "user_app.tasks.task_delete_expired_accounts_and_nofity": {
        "queue": REMOVALS_QUEUE_NAME
    },
    "user_app.tasks.wrapper_task_notify_first_reminder": {"queue": EMAIL_QUEUE_NAME},
    "user_app.tasks.wrapper_task_notify_second_reminder": {"queue": EMAIL_QUEUE_NAME},
}

app.autodiscover_tasks()
