"""
Module for creating periodic tasks using django-celery-beat.
"""

import json

from django_celery_beat.models import CrontabSchedule, PeriodicTask
from user_app.constants.celery import (
    DELETE_EXPIRED_ACCOUNT_AND_NOTIFY_TASK_NAME,
    REMOVE_EXPIRED_CODE_TASK_NAME,
    REMOVE_EXPIRED_TOKENS_TASK_NAME,
    WRAPPER_NOTIFY_FIRST_REMINDER_TASK_NAME,
    WRAPPER_NOTIFY_SECOND_REMINDER_TASK_NAME,
)


def create_periodic_task_for_expired_codes_removal() -> None:
    """
    Creates a periodic task that removes expired verification codes from the database.

    This function creates a scheduled task that runs daily at 3:00 AM to execute
    the `task_remove_exp_code` task, which removes expired account activation codes,
    email change codes, and reset password codes from the database.

    It ensures that the task is only created once and prevents duplication of the task
    in the PeriodicTask table.

    Guarantees:
        - The task will only be created once, preventing duplication in the
          `PeriodicTask` table.

    Schedule:
        - Frequency: Daily
        - Time: 3:00 AM
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


def create_periodic_task_for_expired_tokens_removal() -> None:
    """
    Creates a periodic task that removes expired tokens from the database.

    This function creates a scheduled task that runs daily at 3:00 AM to execute
    the `task_remove_exp_token` task, which removes expired validation tokens and
    blacklisted tokens from the database.

    It ensures that the task is only created once and prevents duplication of the task
    in the PeriodicTask table.

    Guarantees:
        - The task will only be created once, preventing duplication in the
          `PeriodicTask` table.

    Schedule:
        - Frequency: Daily
        - Time: 3:00 AM
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


def create_periodic_task_for_notify_first_reminder() -> None:
    """
    Creates a periodic task to send the first activation reminder.

    This function schedules a task that runs daily at 9:00 AM to execute
    `wrapper_task_notify_first_reminder`, sending reminder emails to accounts who have not
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

    if not PeriodicTask.objects.filter(
        name=WRAPPER_NOTIFY_FIRST_REMINDER_TASK_NAME
    ).exists():
        PeriodicTask.objects.create(
            crontab=schedule,
            name=WRAPPER_NOTIFY_FIRST_REMINDER_TASK_NAME,
            task="user_app.tasks.wrapper_task_notify_first_reminder",
            args=json.dumps([]),
        )


def create_periodic_task_for_notify_second_reminder() -> None:
    """
    Creates a periodic task to send the second activation reminder.

    This function schedules a task that runs daily at 9:00 AM to execute
    `wrapper_task_notify_second_reminder`, sending a final reminder email to accounts who have
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

    if not PeriodicTask.objects.filter(
        name=WRAPPER_NOTIFY_SECOND_REMINDER_TASK_NAME
    ).exists():
        PeriodicTask.objects.create(
            crontab=schedule,
            name=WRAPPER_NOTIFY_SECOND_REMINDER_TASK_NAME,
            task="user_app.tasks.wrapper_task_notify_second_reminder",
            args=json.dumps([]),
        )


def create_periodic_task_for_delete_and_notify() -> None:
    """
    Creates a periodic task that deletes expired accounts and notifies accounts,
    daily at 00:00.

    Guarantees:
        - The task will only be created once, preventing duplication in the
          `PeriodicTask` table.

    Schedule:
        - Frequency: Daily
        - Time: 00:00 AM
    """
    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute="0",
        hour="0",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
    )

    if not PeriodicTask.objects.filter(
        name=DELETE_EXPIRED_ACCOUNT_AND_NOTIFY_TASK_NAME
    ).exists():
        PeriodicTask.objects.create(
            crontab=schedule,
            name=DELETE_EXPIRED_ACCOUNT_AND_NOTIFY_TASK_NAME,
            task="user_app.tasks.task_delete_expired_accounts_and_notify",
            args=json.dumps([]),
        )
