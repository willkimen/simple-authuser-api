from datetime import timedelta
from smtplib import SMTPException
from unittest.mock import MagicMock, patch

import pytest
import time_machine
from celery import states
from celery.result import EagerResult
from django.utils import timezone
from account_auth.models import FailedTaskModel, AccountModel
from account_auth.models.account import PendingAccountsModel
from account_auth.tasks import task_notify_first_reminder
from account_auth.tests.constants import (
    LOGGER_EMAIL_TASK_ERROR_FUNCTION_PATCH,
    NOTIFY_ACTIVATION_ACCOUNT_REMINDER_FUNCTION_TO_PATCH,
    TASKS_MODULE_PATH,
)

# ========== Constants ==================
ACCOUNT_DATA = {
    "first_name": "Fake Name",
    "last_name": "Fake Last",
    "email": "fake@email.com",
    "is_active": False,
    "password": "FAKEfake123!",
}

EMAILS_INACTIVE_ACCOUNTS = [
    "fake1@email.com",
    "fake2@email.com",
    "fake3@email.com",
]

TODAY_BEFORE_CUTOFF = timezone.now().replace(
    hour=(PendingAccountsModel.CUTOFF_HOUR - 1), minute=00, second=0, microsecond=0
)

FIRST_REMINDER_DAY = timezone.now() + timedelta(
    days=PendingAccountsModel.REMINDER_DAYS["before_cutoff"]["first_day"]
)

SECOND_REMINDER_DAY = timezone.now() + timedelta(
    days=PendingAccountsModel.REMINDER_DAYS["before_cutoff"]["second_day"]
)

# Sets the deadline date for account activation.
ACTIVATION_DEADLINE_DAY = SECOND_REMINDER_DAY.replace(
    hour=23, minute=59, second=59, microsecond=0
)


# ============== Fixtures ==============
@pytest.fixture
def create_accounts_for_reminder():
    """
    Fixture that creates multiple accounts in the database for reminder.

    This fixture:
        - Creates accounts who registered **today**, before the cutoff time
          defined by `CUTOFF_HOUR`.

    Usage:
        - This fixture is useful for testing scenarios where accounts' registration
          dates affect whether they should receive activation reminders.
        - Accounts created before the cutoff hour will have their reminder dates
          set accordingly.

    Details:
        - The batch of accounts (created today before `CUTOFF_HOUR`) will have
          their `PendingAccountsModel` entries created with the corresponding
          reminder dates.

    Example:
        - The accounts registered before `CUTOFF_HOUR` will be eligible for
          today's reminders.
    """
    with time_machine.travel(TODAY_BEFORE_CUTOFF):
        for email in EMAILS_INACTIVE_ACCOUNTS:
            ACCOUNT_DATA["email"] = email
            account = AccountModel.objects.create_user(**ACCOUNT_DATA)
            PendingAccountsModel.objects.create(account=account)


# =============== Tests ================
@pytest.mark.django_db
def test_task_notify_first_reminder_success(create_accounts_for_reminder):
    """
    Test the successful execution of the task_notify_first_reminder task.

    This test verifies that the task successfully sends an email and
    returns the correct sent count. The expected value is 1, indicating that
    one email has been sent.
    """
    with time_machine.travel(FIRST_REMINDER_DAY):
        expected_success_send_email = 1

        result: EagerResult = task_notify_first_reminder.apply(
            args=(EMAILS_INACTIVE_ACCOUNTS, ACTIVATION_DEADLINE_DAY)
        )
        actual_sent_count: int = result.get()

        assert expected_success_send_email == actual_sent_count
        assert result.status == states.SUCCESS


@pytest.mark.django_db
@patch(
    f"{TASKS_MODULE_PATH}.{NOTIFY_ACTIVATION_ACCOUNT_REMINDER_FUNCTION_TO_PATCH}",
    side_effect=SMTPException(),
)
@patch(f"{TASKS_MODULE_PATH}.{LOGGER_EMAIL_TASK_ERROR_FUNCTION_PATCH}")
def test_task_notify_first_reminder_failure(
    mock_logger_email_task_error: MagicMock, mock_notify_first_reminder: MagicMock
):
    """
    Test the failure scenario for the task_notify_first_reminder task.
    """
    result: EagerResult = task_notify_first_reminder.apply(
        args=(EMAILS_INACTIVE_ACCOUNTS, ACTIVATION_DEADLINE_DAY)
    )

    with pytest.raises(SMTPException):
        result.get()

    assert result.status == states.FAILURE
    mock_logger_email_task_error.assert_called()


@pytest.mark.django_db
@patch(
    f"{TASKS_MODULE_PATH}.{NOTIFY_ACTIVATION_ACCOUNT_REMINDER_FUNCTION_TO_PATCH}",
    side_effect=SMTPException(),
)
def test_task_data_is_recorded_when_it_fails(mock_notify_first_reminder: MagicMock):
    """Tests if task failure data is recorded in the FailedTaskModel."""
    result: EagerResult = task_notify_first_reminder.apply(
        args=(EMAILS_INACTIVE_ACCOUNTS, ACTIVATION_DEADLINE_DAY)
    )

    with pytest.raises(SMTPException):
        result.get()

    failed_task_model = FailedTaskModel.objects.first()

    assert failed_task_model is not None
    assert failed_task_model.task_id == result.id
    assert failed_task_model.args == [
        EMAILS_INACTIVE_ACCOUNTS,
        ACTIVATION_DEADLINE_DAY.isoformat().replace("+00:00", "Z"),
    ]
    assert failed_task_model.kwargs == {}
    assert failed_task_model.created_at is not None
