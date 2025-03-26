"""
Test for the `create_periodic_task_for_notify_expired_account_deletion` function.

Scenario:
- The function is called to register a periodic task in Celery Beat.
- The task should be scheduled to run daily at 09:00.
"""

import pytest
from django_celery_beat.models import PeriodicTask
from user_app.constants.celery_constants import (
    NOTIFY_EXPIRED_ACCOUNT_DELETION_TASK_NAME,
)
from user_app.periodic_tasks import (
    create_periodic_task_for_notify_expired_account_deletion,
)


@pytest.mark.django_db
def test_create_periodic_task_for_notify_expired_account_deletion():
    create_periodic_task_for_notify_expired_account_deletion()

    task = PeriodicTask.objects.filter(
        name=NOTIFY_EXPIRED_ACCOUNT_DELETION_TASK_NAME
    ).first()
    assert task is not None
    assert task.crontab.minute == "0"
    assert task.crontab.hour == "9"
