from unittest.mock import MagicMock, patch

import pytest
from django.conf import settings
from user_app.models import ResetPasswordCodeModel
from user_app.tests.constants import (
    EMAIL_MULTI_CLASS_TO_PATCH,
    EMAIL_SERVICE_MODULE_PATH,
    FAKE_CODE,
    GENERATE_RANDOM_CODE_FUNCTION_TO_PATCH,
)
from user_app.utils.email_service import send_reset_password_code_by_email


# =============== Tests ================
@pytest.mark.skipif(
    settings.DEBUG != True,
    reason="Test ignored. Not in development environment.",
)
@pytest.mark.django_db
def test_success_send_email_development(deactivated_user):
    """
    Test to verify email sending in the development environment.

    This test uses Django's 'console.EmailBackend', which simulates sending emails
    by displaying the content in the console instead of actually sending them. The
    purpose of this test is to ensure that the function is working correctly and
    that it returns the expected number of emails sent.

    **Pre-conditions**:
    - The environment must be configured as "development".
    - A user (deactivated_user) must be provided for the test.

    **Expected Results**:
    - The test passes if the function returns the correct number of emails sent
      (1). If the returned number is different, the test fails, indicating that
      there was an issue with sending the email.

    **Notes**:
    - This test should not be executed in environments other than
      development, as the goal is to validate the email sending logic
      in a safe environment without the risk of sending real emails.
    """
    expected_send_count = 1
    actual_sent_count = send_reset_password_code_by_email(deactivated_user.email)
    assert expected_send_count == actual_sent_count


@pytest.mark.django_db
@patch(f"{EMAIL_SERVICE_MODULE_PATH}.{EMAIL_MULTI_CLASS_TO_PATCH}")
@patch(
    f"{EMAIL_SERVICE_MODULE_PATH}.{GENERATE_RANDOM_CODE_FUNCTION_TO_PATCH}",
    return_value=FAKE_CODE,
)
def test_success_send_email_create_code_in_database(
    generate_random_code_function_mock: MagicMock,
    EmailMultiAlternativesMock: MagicMock,
    deactivated_user,
):
    """
    Tests if the password reset code is successfully sent via email
    and if the code is created in the database.

    Verifies that the email sending function is called and that the
    password reset code has been stored in the ResetPasswordCodeModel table.
    """
    # Returns a mocked instance of the EmailMultiAlternatives class
    mock_email_multi_instance = EmailMultiAlternativesMock.return_value

    send_reset_password_code_by_email(deactivated_user.email)

    mock_email_multi_instance.send.assert_called()

    assert ResetPasswordCodeModel.objects.filter(code=FAKE_CODE).exists()
