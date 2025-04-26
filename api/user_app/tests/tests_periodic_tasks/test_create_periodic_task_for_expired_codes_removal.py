"""
Test for the `create_periodic_task_for_expired_codes_removal` function.

This test ensures that the `create_periodic_task_for_expired_codes_removal` 
function correctly creates a periodic task in the database for removing 
expired codes.

Scenario:
- The function is called to register a periodic task in Celery Beat.
- The task should be scheduled to run daily at 03:00.
"""

import pytest
from django_celery_beat.models import PeriodicTask
from user_app.constants.celery import REMOVE_EXPIRED_CODE_TASK_NAME
from user_app.periodic_tasks import create_periodic_task_for_expired_codes_removal


@pytest.mark.django_db
def test_create_periodic_task_for_expired_codes_removal():
    create_periodic_task_for_expired_codes_removal()

    task = PeriodicTask.objects.filter(name=REMOVE_EXPIRED_CODE_TASK_NAME).first()
    assert task is not None
    assert task.crontab.minute == "0"
    assert task.crontab.hour == "3"
