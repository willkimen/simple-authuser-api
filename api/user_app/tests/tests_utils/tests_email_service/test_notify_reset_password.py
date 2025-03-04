import smtplib
from unittest.mock import MagicMock, patch

import pytest
from user_app.tests.constants import (
    EMAIL_SERVICE_MODULE_PATH,
    PASSWORD_RESET_NOTIFICATION_EMAIL_CLASS_TO_PATCH,
    SEND_WITH_ERROR_HANDLING_METHOD_TO_PATCH,
)
from user_app.utils.email_service import notify_reset_password

# ========== Objects and constants ============
EMAIL = "fakeemail@email.com"


# =============== Tests ================
@pytest.mark.django_db
def test_success_send_email():
    """
    The purpose of this test is to ensure that the function is working correctly and
    that it returns the expected number of emails sent.

    **Expected Results**:
    - The test passes if the function returns the correct number of emails sent
      (1). If the returned number is different, the test fails, indicating that
      there was an issue with sending the email.
    """
    expected_send_count = 1
    actual_sent_count = notify_reset_password(EMAIL)
    assert expected_send_count == actual_sent_count


@pytest.mark.django_db
@patch(
    f"{EMAIL_SERVICE_MODULE_PATH}."
    f"{PASSWORD_RESET_NOTIFICATION_EMAIL_CLASS_TO_PATCH}."
    f"{SEND_WITH_ERROR_HANDLING_METHOD_TO_PATCH}",
    side_effect=smtplib.SMTPException(),
)
def test_failure_send_email(mock_send_with_error_handling: MagicMock):
    """
    The purpose of this test is to verify that the function correctly handles email
    sending failures by raising an appropriate exception.
    """
    with pytest.raises(smtplib.SMTPException):
        notify_reset_password(EMAIL)
