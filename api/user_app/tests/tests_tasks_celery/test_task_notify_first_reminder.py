from datetime import timedelta
from smtplib import SMTPException
from unittest.mock import MagicMock, patch

import pytest
import time_machine
from celery.exceptions import Retry
from django.utils import timezone
from user_app.models import UserProfileModel
from user_app.models.user_models import PendingAccounts
from user_app.tasks import task_notify_first_reminder
from user_app.tests.constants import (
    NOTIFY_FIRST_REMINDER_FUNCTION_TO_PATCH,
    TASKS_MODULE_PATH,
)

# ========== Constants ==================
USER_DATA = {
    "first_name": "Fake Name",
    "last_name": "Fake Last",
    "email": "fake@email.com",
    "is_active": False,
    "password": "FAKEfake123!",
}


# List of email addresses that should receive a reminder today,
# because their reminder date is today.
expected_reminder_emails_today = [
    "fake1@email.com",
    "fake2@email.com",
    "fake3@email.com",
]


# ============== Fixtures ==============
@pytest.fixture
def create_users_for_reminder():
    """
    Fixture that creates multiple users in the database for reminder.

    This fixture:
        - Creates users who registered **today**, before the cutoff time
          defined by `DAY_CUTOFF_HOUR`.

    Usage:
        - This fixture is useful for testing scenarios where users' registration
          dates affect whether they should receive activation reminders.
        - Users created before the cutoff hour will have their reminder dates
          set accordingly.

    Details:
        - The batch of users (created today before `DAY_CUTOFF_HOUR`) will have
          their `PendingAccounts` entries created with the corresponding reminder dates.

    Example:
        - The users registered before `DAY_CUTOFF_HOUR` will be eligible for
          today's reminders.
    """
    before_day_cutoff_hour = timezone.now().replace(
        hour=(PendingAccounts.DAY_CUTOFF_HOUR - 1), minute=00, second=0, microsecond=0
    )

    with time_machine.travel(before_day_cutoff_hour):
        for email in expected_reminder_emails_today:
            USER_DATA["email"] = email
            user = UserProfileModel.objects.create_user(**USER_DATA)
            PendingAccounts.objects.create(user=user)


# =============== Tests ================
@pytest.mark.django_db
def test_task_notify_first_reminder_success(create_users_for_reminder):
    """
    Test the successful execution of the task_notify_first_reminder task.

    This test verifies that the task successfully sends an email and
    returns the correct sent count. The expected value is 1, indicating that
    one email has been sent.
    """

    first_reminder_day = timezone.now() + timedelta(
        days=PendingAccounts.FIRST_REMINDER_DAYS_BEFORE_DAY_CUTOFF_HOUR
    )

    with time_machine.travel(first_reminder_day):
        expected_success_send_email = 1
        actual_sent_count = task_notify_first_reminder()
        assert expected_success_send_email == actual_sent_count


@pytest.mark.django_db
def test_task_notify_first_reminder_not_reminders():
    """
    Tests the scenario where there are no users to notify, when
    no reminders are scheduled for the test day.

    This test checks if the task_notify_first_reminder function returns -1
    when there are no users with reminders scheduled for the current day.

    If no emails are to be sent, the function should return -1.

    Expected result:
        - If there are no users to notify, `expected_send_count` should be -1.
    """
    expected_send_count = -1
    actual_sent_count = task_notify_first_reminder()
    assert expected_send_count == actual_sent_count


@pytest.mark.django_db
@patch(
    f"{TASKS_MODULE_PATH}.{NOTIFY_FIRST_REMINDER_FUNCTION_TO_PATCH}",
    side_effect=SMTPException(),
)
@patch.object(task_notify_first_reminder, "retry", side_effect=Retry())
def test_task_notify_first_reminder_failure(
    mock_retry: MagicMock, mock_notify_first_reminder: MagicMock
):
    """
    Test the failure scenario for the task_notify_first_reminder task.

    This test simulates an SMTPException being raised when the
    notify_first_reminder function is called. It then verifies that
    the task retries the operation by calling the `retry()` method once.
    Finally, it checks that the retry exception (`Retry`) is raised.
    """
    with pytest.raises(Retry):
        task_notify_first_reminder()

    mock_retry.assert_called_once()
