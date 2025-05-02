import smtplib
from unittest.mock import MagicMock, patch

import pytest
from user_app.models import ResetPasswordCodeModel
from user_app.tests.constants import (
    EMAIL_SERVICE_MODULE_PATH,
    RESET_PASSWORD_CODE_EMAIL_CLASS_TO_PATCH,
    SEND_WITH_ERROR_HANDLING_METHOD_TO_PATCH,
)
from user_app.email.email_service import send_reset_password_code


# =============== Tests ================
@pytest.mark.django_db
def test_success_send_email(deactivated_account):
    """
    The purpose of this test is to ensure that the function is working correctly and
    that it returns the expected number of emails sent.

    **Expected Results**:
    - The test passes if the function returns the correct number of emails sent
      (1). If the returned number is different, the test fails, indicating that
      there was an issue with sending the email.
    """
    expected_send_count = 1
    actual_sent_count = send_reset_password_code(deactivated_account.email)
    assert expected_send_count == actual_sent_count


@pytest.mark.django_db
def test_success_send_email_create_code_in_database(deactivated_account):
    """
    Tests if the password reset code is successfully sent via email
    and if the code is created in the database.

    Verifies that the email sending function is called and that the
    password reset code has been stored in the ResetPasswordCodeModel table.
    """
    send_reset_password_code(deactivated_account.email)

    assert ResetPasswordCodeModel.objects.filter(
        account_id=deactivated_account.email
    ).exists()
    assert (
        ResetPasswordCodeModel.objects.filter(account_id=deactivated_account.email).count()
        == 1
    )


@pytest.mark.django_db
@patch(
    f"{EMAIL_SERVICE_MODULE_PATH}."
    f"{RESET_PASSWORD_CODE_EMAIL_CLASS_TO_PATCH}."
    f"{SEND_WITH_ERROR_HANDLING_METHOD_TO_PATCH}",
    side_effect=smtplib.SMTPException(),
)
def test_failure_send_email(mock_send_with_error_handling: MagicMock, deactivated_account):
    """
    The purpose of this test is to verify that the function correctly handles email
    sending failures by raising an appropriate exception.
    """
    with pytest.raises(smtplib.SMTPException):
        send_reset_password_code(deactivated_account.email)
