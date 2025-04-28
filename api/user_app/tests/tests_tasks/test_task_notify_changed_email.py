from smtplib import SMTPException
from unittest.mock import MagicMock, patch

import pytest
from celery import states
from celery.result import EagerResult
from user_app.models import FailedTaskModel
from user_app.tasks import task_notify_changed_email
from user_app.tests.constants import (
    LOGGER_EMAIL_TASK_ERROR_FUNCTION_PATCH,
    NOTIFY_CHANGED_EMAIL_FUNCTION_TO_PATCH,
    TASKS_MODULE_PATH,
)

NEW_EMAIL = "newemail@email.com"


@pytest.mark.django_db
def test_task_notify_changed_email_success():
    """
    Test the successful execution of the task_notify_changed_email.

    This test verifies that the task successfully sends email and
    returns the correct sent count. The expected value is 1, indicating that
    one email has been sent.
    """
    expected_success_send_email = 1

    result: EagerResult = task_notify_changed_email.apply(args=(NEW_EMAIL,))
    actual_sent_count: int = result.get()

    assert expected_success_send_email == actual_sent_count
    assert result.status == states.SUCCESS


@pytest.mark.django_db
@patch(
    f"{TASKS_MODULE_PATH}.{NOTIFY_CHANGED_EMAIL_FUNCTION_TO_PATCH}",
    side_effect=SMTPException(),
)
@patch(f"{TASKS_MODULE_PATH}.{LOGGER_EMAIL_TASK_ERROR_FUNCTION_PATCH}")
def test_task_notify_changed_email_failure(
    mock_logger_email_task_error: MagicMock,
    mock_notify_changed_email: MagicMock,
):
    """
    Test the failure scenario for the task_notify_chaged_email task.
    """
    result: EagerResult = task_notify_changed_email.apply(args=(NEW_EMAIL,))

    with pytest.raises(SMTPException):
        result.get()

    assert result.state == states.FAILURE
    mock_logger_email_task_error.assert_called()


@pytest.mark.django_db
@patch(
    f"{TASKS_MODULE_PATH}.{NOTIFY_CHANGED_EMAIL_FUNCTION_TO_PATCH}",
    side_effect=SMTPException(),
)
def test_task_data_is_recorded_when_it_fails(mock_notify_changed_email: MagicMock):
    """Tests if task failure data is recorded in the FailedTaskModel."""
    result: EagerResult = task_notify_changed_email.apply(args=(NEW_EMAIL,))

    with pytest.raises(SMTPException):
        result.get()

    failed_task_model = FailedTaskModel.objects.first()

    assert failed_task_model is not None
    assert failed_task_model.task_id == result.id
    assert failed_task_model.args == [NEW_EMAIL]
    assert failed_task_model.kwargs == {}
    assert failed_task_model.created_at is not None
