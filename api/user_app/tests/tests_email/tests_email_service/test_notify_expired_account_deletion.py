import smtplib
from unittest.mock import MagicMock, patch

import pytest
from user_app.email.email_service import notify_expired_account_deletion
from user_app.models import UsersPendingDeletionNotificationModel
from user_app.tests.constants import (
    EMAIL_SERVICE_MODULE_PATH,
    EXPIRED_ACCOUNT_DELETION_EMAIL_CLASS_TO_PATCH,
    SEND_WITH_ERROR_HANDLING_METHOD_TO_PATCH,
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


# =============== Tests ================
@pytest.mark.django_db
def test_success_send_email(persistent_emails: list[str]):
    """
    The purpose of this test is to ensure that the function is working correctly and
    that it returns the expected number of emails sent.

    Expected Results:
    - The test passes if the function returns the correct number of emails sent
      (1). If the returned number is different, the test fails, indicating that
      there was an issue with sending the email.
    """
    expected_send_count = 1
    actual_sent_count, _ = notify_expired_account_deletion()
    assert expected_send_count == actual_sent_count


@pytest.mark.django_db
@patch(
    f"{EMAIL_SERVICE_MODULE_PATH}."
    f"{EXPIRED_ACCOUNT_DELETION_EMAIL_CLASS_TO_PATCH}."
    f"{SEND_WITH_ERROR_HANDLING_METHOD_TO_PATCH}",
    side_effect=smtplib.SMTPException(),
)
def test_failure_send_email(
    mock_send_with_error_handling: MagicMock, persistent_emails: list[str]
):
    """
    The purpose of this test is to verify that the function correctly handles email
    sending failures by raising an appropriate exception.
    """
    with pytest.raises(smtplib.SMTPException):
        notify_expired_account_deletion()


@pytest.mark.django_db
def test_after_notification_emails_are_deleted(persistent_emails: list[str]):
    """
    After notifications are sent to users, the emails should be deleted.
    """
    for email in persistent_emails:
        assert UsersPendingDeletionNotificationModel.objects.filter(
            email=email
        ).exists()

    notify_expired_account_deletion()

    for email in persistent_emails:
        assert not UsersPendingDeletionNotificationModel.objects.filter(
            email=email
        ).exists()


@pytest.mark.django_db
def test_does_not_send_notification_when_there_are_no_users():
    """
    When there are no users to be notified, returns -1.
    """
    expected_send_count = -1
    actual_sent_count, _ = notify_expired_account_deletion()
    assert expected_send_count == actual_sent_count
