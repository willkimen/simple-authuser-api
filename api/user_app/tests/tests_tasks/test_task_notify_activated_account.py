from smtplib import SMTPException
from unittest.mock import MagicMock, patch

import pytest
from celery.exceptions import Retry
from user_app.tasks import task_notify_activated_account
from user_app.tests.constants import (
    NOTIFY_ACTIVATED_ACCOUNT_FUNCTION_TO_PATCH,
    TASKS_MODULE_PATH,
)

EMAIL = "fakeemail@email.com"


@pytest.mark.django_db
def test_task_notify_activated_account_success():
    """
    Test the successful execution of the task_notify_activated_account task.

    This test verifies that the task successfully sends an email and
    returns the correct sent count. The expected value is 1, indicating that
    one email has been sent.
    """
    expected_success_send_email = 1
    actual_sent_count = task_notify_activated_account(EMAIL)
    assert expected_success_send_email == actual_sent_count


@pytest.mark.django_db
@patch(
    f"{TASKS_MODULE_PATH}.{NOTIFY_ACTIVATED_ACCOUNT_FUNCTION_TO_PATCH}",
    side_effect=SMTPException(),
)
@patch.object(task_notify_activated_account, "retry", side_effect=Retry())
def test_task_notify_activated_account_failure(
    mock_retry: MagicMock, mock_notify_activated_account: MagicMock
):
    """
    Test the failure scenario for the task_notify_activated_account task.

    This test simulates an SMTPException being raised when the
    notify_activated_account function is called. It then verifies that
    the task retries the operation by calling the `retry()` method once.
    Finally, it checks that the retry exception (`Retry`) is raised.
    """
    with pytest.raises(Retry):
        task_notify_activated_account(EMAIL)

    mock_retry.assert_called_once()
