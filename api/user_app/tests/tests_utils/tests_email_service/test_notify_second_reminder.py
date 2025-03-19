import smtplib
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
import time_machine
from django.utils import timezone
from user_app.models import UserProfileModel
from user_app.models.user_models import PendingAccountsModel
from user_app.tests.constants import (
    DEACTIVATED_ACCOUNT_NOTIFICATION_EMAIL_CLASS_TO_PATCH,
    EMAIL_SERVICE_MODULE_PATH,
    SEND_WITH_ERROR_HANDLING_METHOD_TO_PATCH,
)
from user_app.utils.email_service import notify_second_reminder

# ========== Constants ==================
USER_DATA = {
    "first_name": "Fake Name",
    "last_name": "Fake Last",
    "email": "fake@email.com",
    "is_active": False,
    "password": "FAKEfake123!",
}

EMAILS_INACTIVE_USERS = [
    "fake1@email.com",
    "fake2@email.com",
    "fake3@email.com",
]

# Sets today's date and a time before the cutoff hour.
TODAY_BEFORE_CUTOFF = timezone.now().replace(
    hour=(PendingAccountsModel.CUTOFF_HOUR - 1), minute=00, second=0, microsecond=0
)

# Set the date for the second reminder
SECOND_REMINDER_DAY = timezone.now() + timedelta(
    days=PendingAccountsModel.REMINDER_DAYS["before_cutoff"]["second_day"]
)


# ============== Fixtures ==============
@pytest.fixture
def create_users_for_reminder():
    """
    Fixture that creates multiple users in the database for reminder.

    This fixture:
        - Creates users who registered **today**, before the cutoff time
          defined by `CUTOFF_HOUR`.

    Usage:
        - This fixture is useful for testing scenarios where users' registration
          dates affect whether they should receive activation reminders.
        - Users created before the cutoff hour will have their reminder dates
          set accordingly.

    Details:
        - The batch of users (created today before `CUTOFF_HOUR`) will have
          their `PendingAccountsModel` entries created with the corresponding
          reminder dates.

    Example:
        - The users registered before `CUTOFF_HOUR` will be eligible for
          today's reminders.
    """
    with time_machine.travel(TODAY_BEFORE_CUTOFF):
        for email in EMAILS_INACTIVE_USERS:
            USER_DATA["email"] = email
            user = UserProfileModel.objects.create_user(**USER_DATA)
            PendingAccountsModel.objects.create(user=user)


# =============== Tests ================
@pytest.mark.django_db
def test_success_send_email(create_users_for_reminder):
    """
    Tests the successful sending of the second reminder email to users
    who have their second reminder scheduled for the test day.

    The test performs the following:
        1. Creates users whose activation reminders are scheduled
           for the test day.
        2. Verifies that the `notify_second_reminder` function is called correctly.

    The `notify_second_reminder` function should return 1 when an email
    is successfully sent to a user.

    Expected result:
        - If a user needs to be notified, `expected_send_count` should be 1.
    """

    with time_machine.travel(SECOND_REMINDER_DAY):
        expected_send_count = 1
        actual_sent_count = notify_second_reminder()
        assert expected_send_count == actual_sent_count


@pytest.mark.django_db
def test_there_are_not_reminders_to_sent():
    """
    Tests the scenario where there are no users to notify, when
    no reminders are scheduled for the test day.

    This test checks if the `notify_second_reminder` function returns -1
    when there are no users with reminders scheduled for the current day.

    If no emails are to be sent, the function should return -1.

    Expected result:
        - If there are no users to notify, `expected_send_count` should be -1.
    """
    expected_send_count = -1
    actual_sent_count = notify_second_reminder()
    assert expected_send_count == actual_sent_count


@pytest.mark.django_db
@patch(
    f"{EMAIL_SERVICE_MODULE_PATH}."
    f"{DEACTIVATED_ACCOUNT_NOTIFICATION_EMAIL_CLASS_TO_PATCH}."
    f"{SEND_WITH_ERROR_HANDLING_METHOD_TO_PATCH}",
    side_effect=smtplib.SMTPException(),
)
def test_failure_send_email(
    mock_send_with_error_handling: MagicMock, create_users_for_reminder
):
    """
    The purpose of this test is to verify that the function correctly handles email
    sending failures by raising an appropriate exception.
    """
    with time_machine.travel(SECOND_REMINDER_DAY):
        with pytest.raises(smtplib.SMTPException):
            notify_second_reminder()
