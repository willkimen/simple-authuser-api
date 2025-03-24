"""
Test for the `create_periodic_task_for_delete_expired_accounts` function.

This test ensures that the `create_periodic_task_for_delete_expired_accounts` 
function correctly creates a periodic task in the database for removing 
expired accounts.

Scenario:
- The function is called to register a periodic task in Celery Beat.
- The task should be scheduled to run daily at 00:00.
"""

import pytest
from django_celery_beat.models import PeriodicTask
from user_app.constants.celery_constants import REMOVE_EXPIRED_ACCOUNT_TASK_NAME
from user_app.periodic_tasks import create_periodic_task_for_delete_expired_accounts


@pytest.mark.django_db
def test_create_periodic_task_for_delete_expired_accounts():
    create_periodic_task_for_delete_expired_accounts()

    task = PeriodicTask.objects.filter(name=REMOVE_EXPIRED_ACCOUNT_TASK_NAME).first()
    assert task is not None
    assert task.crontab.minute == "0"
    assert task.crontab.hour == "0"
