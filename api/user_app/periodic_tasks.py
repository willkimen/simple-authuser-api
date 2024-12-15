"""
Module for creating periodic tasks in Django using Celery and django-celery-beat.

Description:
This module contains functions to create scheduled periodic tasks that 
automatically remove expired codes and tokens from the database. 
The tasks are scheduled to run daily at 3:00 AM.

Usage:
These functions can be called during database migrations 
to set up the tasks automatically, ensuring the scheduled removal of expired data.

Dependencies:
- Celery: For task scheduling and execution.
- django-celery-beat: For managing periodic tasks and scheduling.
"""

import json

from django_celery_beat.models import CrontabSchedule, PeriodicTask
from user_app.constants.periodic_tasks_names import (
    REMOVE_EXPIRED_CODE_TASK_NAME,
    REMOVE_EXPIRED_TOKENS_TASK_NAME,
)


def create_periodic_task_for_expired_codes_removal(apps, schema_editor):
    """
    Creates a periodic task that removes expired codes from the database.

    This function creates a scheduled task that runs daily at 3:00 AM to execute
    the `task_remove_exp_code` task, which removes expired account activation codes,
    email change codes, and reset password codes from the database.

    It ensures that the task is only created once and prevents duplication of the task
    in the PeriodicTask table.
    """
    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute="0",
        hour="3",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
    )

    if not PeriodicTask.objects.filter(name=REMOVE_EXPIRED_CODE_TASK_NAME).exists():
        PeriodicTask.objects.create(
            crontab=schedule,
            name=REMOVE_EXPIRED_CODE_TASK_NAME,
            task="teste_app.tasks.task_remove_exp_code",
            args=json.dumps([]),
        )


def create_periodic_task_for_expired_tokens_removal(apps, schema_editor):
    """
    Creates a periodic task that removes expired tokens from the database.

    This function creates a scheduled task that runs daily at 3:00 AM to execute
    the `task_remove_exp_token` task, which removes expired validation tokens and
    blacklisted tokens from the database.

    It ensures that the task is only created once and prevents duplication of the task
    in the PeriodicTask table.
    """
    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute="0",
        hour="3",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
    )

    if not PeriodicTask.objects.filter(name=REMOVE_EXPIRED_TOKENS_TASK_NAME).exists():
        PeriodicTask.objects.create(
            crontab=schedule,
            name=REMOVE_EXPIRED_TOKENS_TASK_NAME,
            task="teste_app.tasks.task_remove_exp_token",
            args=json.dumps([]),
        )
