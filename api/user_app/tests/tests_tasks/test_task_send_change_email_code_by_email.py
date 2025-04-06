from smtplib import SMTPException
from unittest.mock import MagicMock, patch

import pytest
from celery import states
from celery.result import EagerResult
from user_app.tasks import task_send_email_change_code
from user_app.tests.constants import (
    LOGGER_EMAIL_TASK_ERROR_FUNCTION_PATCH,
    SEND_EMAIL_CHANGE_CODE_FUNCTION_TO_PATCH,
    TASKS_MODULE_PATH,
    User,
)

NEW_EMAIL = "newemail@email.com"
ACTUAL_EMAIL = "actualemail@email.com"


@pytest.fixture
def activated_user():
    """
    Fixture to create and return a activated User object.
    """
    return User.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email=ACTUAL_EMAIL,
        password="FAKEpassword10!",
        is_active=True,
    )


@pytest.mark.django_db
def test_task_send_email_change_code_success(activated_user):
    """
    Test the successful execution of the task_send_email_change_code.

    This test verifies that the task successfully sends email and
    returns the correct sent count. The expected value is 1, indicating that
    one email has been sent.
    """
    expected_success_send_email = 1

    result: EagerResult = task_send_email_change_code.apply(
        args=(activated_user.email, NEW_EMAIL)
    )
    actual_sent_count: int = result.get()

    assert expected_success_send_email == actual_sent_count
    assert result.status == states.SUCCESS


@pytest.mark.django_db
@patch(
    f"{TASKS_MODULE_PATH}.{SEND_EMAIL_CHANGE_CODE_FUNCTION_TO_PATCH}",
    side_effect=SMTPException(),
)
@patch(f"{TASKS_MODULE_PATH}.{LOGGER_EMAIL_TASK_ERROR_FUNCTION_PATCH}")
def test_task_send_email_change_code_failure(
    mock_logger_email_task_error: MagicMock,
    mock_send_change_email_code: MagicMock,
    activated_user,
):
    """
    Test the failure scenario for the task_send_email_change_code task.
    """
    result: EagerResult = task_send_email_change_code.apply(
        args=(activated_user.email, NEW_EMAIL)
    )
    with pytest.raises(SMTPException):
        result.get()

    assert result.state == states.FAILURE
    mock_logger_email_task_error.assert_called()
