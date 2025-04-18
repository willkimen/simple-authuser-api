"""
Test for the `create_periodic_task_for_notify_first_reminder` function.
"""

import pytest
from django_celery_beat.models import PeriodicTask
from user_app.constants.celery_constants import WRAPPER_NOTIFY_FIRST_REMINDER_TASK_NAME
from user_app.periodic_tasks import create_periodic_task_for_notify_first_reminder


@pytest.mark.django_db
def test_create_periodic_task_for_notify_first_reminder():
    create_periodic_task_for_notify_first_reminder()

    task = PeriodicTask.objects.filter(
        name=WRAPPER_NOTIFY_FIRST_REMINDER_TASK_NAME
    ).first()
    assert task is not None
    assert task.crontab.minute == "0"
    assert task.crontab.hour == "9"
