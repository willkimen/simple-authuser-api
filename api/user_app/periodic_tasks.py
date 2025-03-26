"""
Module for creating periodic tasks in Django using django-celery-beat.
"""

import json

from django_celery_beat.models import CrontabSchedule, PeriodicTask
from user_app.constants.celery_constants import (
    NOTIFY_EXPIRED_ACCOUNT_DELETION_TASK_NAME,
    NOTIFY_FIRST_REMINDER_TASK_NAME,
    NOTIFY_SECOND_REMINDER_TASK_NAME,
    REMOVE_EXPIRED_ACCOUNT_TASK_NAME,
    REMOVE_EXPIRED_CODE_TASK_NAME,
    REMOVE_EXPIRED_TOKENS_TASK_NAME,
)


def create_periodic_task_for_expired_codes_removal():
    """
    Creates a periodic task that removes expired verification codes from the database.

    This function creates a scheduled task that runs daily at 3:00 AM to execute
    the `task_remove_exp_code` task, which removes expired account verification codes,
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
            task="user_app.tasks.task_remove_exp_code",
            args=json.dumps([]),
        )


def create_periodic_task_for_expired_tokens_removal():
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
            task="user_app.tasks.task_remove_exp_token",
            args=json.dumps([]),
        )


def create_periodic_task_for_notify_first_reminder():
    """
    Creates a periodic task to send the first activation reminder.

    This function schedules a task that runs daily at 9:00 AM to execute
    `task_notify_first_reminder`, sending reminder emails to users who have not
    yet activated their accounts.

    Guarantees:
        - The task will only be created once, preventing duplication in the
          `PeriodicTask` table.

    Schedule:
        - Frequency: Daily
        - Time: 9:00 AM
    """
    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute="0",
        hour="9",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
    )

    if not PeriodicTask.objects.filter(name=NOTIFY_FIRST_REMINDER_TASK_NAME).exists():
        PeriodicTask.objects.create(
            crontab=schedule,
            name=NOTIFY_FIRST_REMINDER_TASK_NAME,
            task="user_app.tasks.task_notify_first_reminder",
            args=json.dumps([]),
        )


def create_periodic_task_for_notify_second_reminder():
    """
    Creates a periodic task to send the second activation reminder.

    This function schedules a task that runs daily at 9:00 AM to execute
    `task_notify_second_reminder`, sending a final reminder email to users who have
    not yet activated their accounts.

    Guarantees:
        - The task will only be created once, preventing duplication in the
          `PeriodicTask` table.

    Schedule:
        - Frequency: Daily
        - Time: 9:00 AM
    """
    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute="0",
        hour="9",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
    )

    if not PeriodicTask.objects.filter(name=NOTIFY_SECOND_REMINDER_TASK_NAME).exists():
        PeriodicTask.objects.create(
            crontab=schedule,
            name=NOTIFY_SECOND_REMINDER_TASK_NAME,
            task="user_app.tasks.task_notify_second_reminder",
            args=json.dumps([]),
        )


def create_periodic_task_for_delete_expired_accounts():
    """
    Creates a periodic task that deletes expired user accounts daily at 00:00.
    """
    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute="0",
        hour="0",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
    )

    if not PeriodicTask.objects.filter(name=REMOVE_EXPIRED_ACCOUNT_TASK_NAME).exists():
        PeriodicTask.objects.create(
            crontab=schedule,
            name=REMOVE_EXPIRED_ACCOUNT_TASK_NAME,
            task="user_app.tasks.task_delete_expired_accounts",
            args=json.dumps([]),
        )


def create_periodic_task_for_notify_expired_account_deletion():
    """
    Creates a periodic task that notify users about removal their accounts
    daily at 09:00.
    """
    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute="0",
        hour="9",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
    )

    if not PeriodicTask.objects.filter(
        name=NOTIFY_EXPIRED_ACCOUNT_DELETION_TASK_NAME
    ).exists():
        PeriodicTask.objects.create(
            crontab=schedule,
            name=NOTIFY_EXPIRED_ACCOUNT_DELETION_TASK_NAME,
            task="user_app.tasks.task_expired_account_deletion",
            args=json.dumps([]),
        )
