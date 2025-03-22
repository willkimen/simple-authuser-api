from smtplib import SMTPException
from unittest.mock import MagicMock, patch

import pytest
from celery.exceptions import Retry
from user_app.tasks import task_send_email_change_code
from user_app.tests.constants import (
    SEND_EMAIL_CHANGE_CODE_FUNCTION_TO_PATCH,
    TASKS_MODULE_PATH,
    User,
)
from user_app.email.email_service import send_email_change_code

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
    actual_sent_count = send_email_change_code(activated_user.email, NEW_EMAIL)
    assert expected_success_send_email == actual_sent_count


@pytest.mark.django_db
@patch(
    f"{TASKS_MODULE_PATH}.{SEND_EMAIL_CHANGE_CODE_FUNCTION_TO_PATCH}",
    side_effect=SMTPException(),
)
@patch.object(task_send_email_change_code, "retry", side_effect=Retry())
def test_task_send_email_change_code_failure(
    mock_retry: MagicMock, mock_send_change_email_code: MagicMock, activated_user
):
    """
    Test the failure scenario for the task_send_email_change_code task.

    This test simulates an SMTPException being raised when the
    send_email_change_code function is called. It then verifies that
    the task retries the operation by calling the `retry()` method once.
    Finally, it checks that the retry exception (`Retry`) is raised.
    """
    with pytest.raises(Retry):
        task_send_email_change_code(activated_user.email, NEW_EMAIL)

    mock_retry.assert_called_once()
