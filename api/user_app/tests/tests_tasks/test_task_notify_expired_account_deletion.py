from smtplib import SMTPException
from unittest.mock import MagicMock, patch

import pytest
from celery import states
from celery.result import EagerResult
from user_app.models import UsersPendingDeletionNotificationModel
from user_app.tasks import task_notify_expired_account_deletion
from user_app.tests.constants import (
    LOGGER_EMAIL_TASK_ERROR_FUNCTION_PATCH,
    NOTIFY_EXPIRED_ACCOUNT_DELETION_FUNCTION_TO_PATCH,
    TASKS_MODULE_PATH,
)


# ========== Fixtures ============
@pytest.fixture
def persistent_emails() -> list[str]:
    """
    This fixture persists some emails in
    UsersPendingDeletionNotificationModel for testing.
    """
    emails = ["fake1@email.com", "fake2@email.com", "fake3@email.com"]
    UsersPendingDeletionNotificationModel.objects.bulk_create(
        [UsersPendingDeletionNotificationModel(email=email) for email in emails]
    )

    return emails


# ========== Tests ============
@pytest.mark.django_db
def test_task_notify_expired_account_deletion_success(persistent_emails: list[str]):
    """
    Test the successful execution of the task_notify_expired_account_deletion.

    This test verifies that the task successfully sends an email and
    returns the correct sent count. The expected value is 1, indicating that
    one email has been sent.
    """
    expected_success_send_email = 1

    result: EagerResult = task_notify_expired_account_deletion.apply()
    actual_sent_count: int = result.get()

    assert expected_success_send_email == actual_sent_count
    assert result.successful() == True
    assert result.status == states.SUCCESS


@pytest.mark.django_db
def test_does_not_send_notification_when_there_are_no_users():
    """
    When there are no users to be notified, returns -1.
    """
    expected_send_count = -1

    result: EagerResult = task_notify_expired_account_deletion.apply()
    actual_sent_count: int = result.get()

    assert expected_send_count == actual_sent_count
    assert result.status == states.SUCCESS


@pytest.mark.django_db
def test_after_notification_emails_are_deleted(persistent_emails: list[str]):
    """
    After notifications are sent to users, the emails should be deleted.
    """
    for email in persistent_emails:
        assert UsersPendingDeletionNotificationModel.objects.filter(
            email=email
        ).exists()

    result: EagerResult = task_notify_expired_account_deletion.apply()

    assert result.successful() == True
    assert result.status == states.SUCCESS
    for email in persistent_emails:
        assert not UsersPendingDeletionNotificationModel.objects.filter(
            email=email
        ).exists()


@pytest.mark.django_db
@patch(
    f"{TASKS_MODULE_PATH}.{NOTIFY_EXPIRED_ACCOUNT_DELETION_FUNCTION_TO_PATCH}",
    side_effect=SMTPException(),
)
@patch(f"{TASKS_MODULE_PATH}.{LOGGER_EMAIL_TASK_ERROR_FUNCTION_PATCH}")
def test_task_notify_reset_password_failure(
    mock_logger_email_task_error: MagicMock,
    mock_notify_expired_account_deletion: MagicMock,
):
    """
    Test the failure scenario for the task_notify_expired_account_deletion task.
    """
    result: EagerResult = task_notify_expired_account_deletion.apply()

    with pytest.raises(SMTPException):
        result.get()

    assert result.state == states.FAILURE
    mock_logger_email_task_error.assert_called()
