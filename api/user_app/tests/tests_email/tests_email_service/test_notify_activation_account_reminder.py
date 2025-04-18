import smtplib
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from user_app.email.email_service import notify_activation_account_reminder
from user_app.tests.constants import (
    DEACTIVATED_ACCOUNT_NOTIFICATION_EMAIL_CLASS_TO_PATCH,
    EMAIL_SERVICE_MODULE_PATH,
    SEND_WITH_ERROR_HANDLING_METHOD_TO_PATCH,
)

# ========== Constants ==================
EMAILS_INACTIVE_USERS = [
    "fake1@email.com",
    "fake2@email.com",
    "fake3@email.com",
]

FAKE_DATETIME = datetime.now()


# =============== Tests ================
@pytest.mark.django_db
def test_success_send_email():
    """
    Tests the successful sending of the reminder email to users.

    The `notify_activation_account_reminder` function should return 1 when an email
    is successfully sent to a user.

    Expected result:
        - If a user needs to be notified, `expected_send_count` should be 1.
    """
    expected_send_count = 1
    actual_sent_count: int = notify_activation_account_reminder(
        emails=EMAILS_INACTIVE_USERS, activation_deadline=FAKE_DATETIME
    )
    assert expected_send_count == actual_sent_count


@pytest.mark.django_db
@patch(
    f"{EMAIL_SERVICE_MODULE_PATH}."
    f"{DEACTIVATED_ACCOUNT_NOTIFICATION_EMAIL_CLASS_TO_PATCH}."
    f"{SEND_WITH_ERROR_HANDLING_METHOD_TO_PATCH}",
    side_effect=smtplib.SMTPException(),
)
def test_failure_send_email(mock_send_with_error_handling: MagicMock):
    """
    The purpose of this test is to verify that the function correctly handles email
    sending failures by raising an appropriate exception.
    """
    with pytest.raises(smtplib.SMTPException):
        notify_activation_account_reminder(emails=[], activation_deadline=FAKE_DATETIME)
