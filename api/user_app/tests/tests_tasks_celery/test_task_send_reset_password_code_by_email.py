from smtplib import SMTPException
from unittest.mock import MagicMock, patch

import pytest
from celery.exceptions import Retry
from user_app.tasks import task_send_reset_password_code_by_email
from user_app.tests.constants import (
    SEND_RESET_PASSWORD_CODE_BY_EMAIL_FUNCTION_TO_PATCH,
    TASKS_MODULE_PATH,
    User,
)


@pytest.fixture
def activated_user():
    """
    Fixture to create and return a deactivated User object.
    """
    return User.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fakeemail@email.com",
        password="FAKEpassword10!",
        is_active=True,
    )


@pytest.mark.django_db
def test_task_send_reset_password_code_by_email_success(activated_user):
    """
    Test the successful execution of the task_send_reset_password_code_by_email task.

    This test verifies that the task successfully sends an email and
    returns the correct sent count. The expected value is 1, indicating that
    one email has been sent.
    """
    expected_success_send_email = 1
    actual_sent_count = task_send_reset_password_code_by_email(activated_user.email)
    assert expected_success_send_email == actual_sent_count


@pytest.mark.django_db
@patch(
    f"{TASKS_MODULE_PATH}.{SEND_RESET_PASSWORD_CODE_BY_EMAIL_FUNCTION_TO_PATCH}",
    side_effect=SMTPException(),
)
@patch.object(task_send_reset_password_code_by_email, "retry", side_effect=Retry())
def test_task_send_reset_password_code_by_email_failure(
    mock_retry: MagicMock, mock_send_reset: MagicMock, activated_user
):
    """
    Test the failure scenario for the task_send_reset_password_code_by_email task.

    This test simulates an SMTPException being raised when the
    send_reset_password_code_by_email function is called. It then verifies that
    the task retries the operation by calling the `retry()` method once.
    Finally, it checks that the retry exception (`Retry`) is raised.
    """
    with pytest.raises(Retry):
        task_send_reset_password_code_by_email(activated_user.email)

    mock_retry.assert_called_once()
