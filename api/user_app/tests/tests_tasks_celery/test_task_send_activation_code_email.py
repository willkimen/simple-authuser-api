from smtplib import SMTPException
from unittest.mock import MagicMock, patch

import pytest
from celery.exceptions import Retry
from user_app.tasks import task_send_account_activation_code
from user_app.tests.constants import (
    SEND_ACCOUNT_ACTIVATION_CODE_FUNCTION_TO_PATCH,
    TASKS_MODULE_PATH,
    User,
)


@pytest.fixture
def deactivated_user():
    """
    Fixture to create and return a deactivated User object.
    """
    return User.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fakeemail@email.com",
        password="FAKEpassword10!",
    )


@pytest.mark.django_db
def test_task_send_account_activation_code_success(deactivated_user):
    """
    Test the successful execution of the task_send_account_activation_code task.

    This test verifies that the task successfully sends an activation email and
    returns the correct sent count. The expected value is 1, indicating that
    one email has been sent.
    """
    expected_success_send_email = 1
    actual_sent_count = task_send_account_activation_code(deactivated_user.email)
    assert expected_success_send_email == actual_sent_count


@pytest.mark.django_db
@patch(
    f"{TASKS_MODULE_PATH}.{SEND_ACCOUNT_ACTIVATION_CODE_FUNCTION_TO_PATCH}",
    side_effect=SMTPException(),
)
@patch.object(task_send_account_activation_code, "retry", side_effect=Retry())
def test_task_send_account_activation_code_failure(
    mock_retry: MagicMock, mock_send_activation: MagicMock, deactivated_user
):
    """
    Test the failure scenario for the task_send_account_activation_code task.

    This test simulates an SMTPException being raised when the
    send_account_activation_code function is called. It then verifies that
    the task retries the operation by calling the `retry()` method once.
    Finally, it checks that the retry exception (`Retry`) is raised.
    """
    with pytest.raises(Retry):
        task_send_account_activation_code(deactivated_user.email)

    mock_retry.assert_called_once()
