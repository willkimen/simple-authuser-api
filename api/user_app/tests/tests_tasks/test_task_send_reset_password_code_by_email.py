from smtplib import SMTPException
from unittest.mock import MagicMock, patch

import pytest
from celery import states
from celery.result import EagerResult
from user_app.tasks import task_send_reset_password_code
from user_app.tests.constants import (
    LOGGER_EMAIL_TASK_ERROR_FUNCTION_PATCH,
    SEND_RESET_PASSWORD_CODE_FUNCTION_TO_PATCH,
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
def test_task_send_reset_password_code_success(activated_user):
    """
    Test the successful execution of the task_send_reset_password_code task.

    This test verifies that the task successfully sends an email and
    returns the correct sent count. The expected value is 1, indicating that
    one email has been sent.
    """
    expected_success_send_email = 1

    result: EagerResult = task_send_reset_password_code.apply(
        args=(activated_user.email,)
    )
    actual_sent_count: int = result.get()

    assert expected_success_send_email == actual_sent_count
    assert result.status == states.SUCCESS


@pytest.mark.django_db
@patch(
    f"{TASKS_MODULE_PATH}.{SEND_RESET_PASSWORD_CODE_FUNCTION_TO_PATCH}",
    side_effect=SMTPException(),
)
@patch(f"{TASKS_MODULE_PATH}.{LOGGER_EMAIL_TASK_ERROR_FUNCTION_PATCH}")
def test_task_send_reset_password_code_failure(
    mock_logger_email_task_error: MagicMock,
    mock_send_reset: MagicMock,
    activated_user,
):
    """
    Test the failure scenario for the task_send_reset_password_code task.
    """
    result: EagerResult = task_send_reset_password_code.apply(
        args=(activated_user.email,)
    )
    with pytest.raises(SMTPException):
        result.get()

    assert result.state == states.FAILURE
    mock_logger_email_task_error.assert_called()
