"""
Test for the `create_periodic_task_for_delete_and_notify` function.

This test ensures that the `create_periodic_task_for_delete_and_notify` 
function correctly creates a periodic task in the database. 

Scenario:
- The function is called to register a periodic task in Celery Beat.
- The task should be scheduled to run daily at 00:00.
"""

import pytest
from django_celery_beat.models import PeriodicTask
from user_app.constants.celery import (
    DELETE_EXPIRED_ACCOUNT_AND_NOTIFY_TASK_NAME,
)
from user_app.periodic_tasks import create_periodic_task_for_delete_and_notify


@pytest.mark.django_db
def test_create_periodic_task_for_delete_and_notify():
    create_periodic_task_for_delete_and_notify()

    task = PeriodicTask.objects.filter(
        name=DELETE_EXPIRED_ACCOUNT_AND_NOTIFY_TASK_NAME
    ).first()
    assert task is not None
    assert task.crontab.minute == "0"
    assert task.crontab.hour == "0"
