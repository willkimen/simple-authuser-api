import os
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model

from user_app.constants.path_for_mock import email_service_module_path
from user_app.models import ResetPasswordCodeModel
from user_app.utils.email_service import send_reset_password_code_by_email

# ========== Objects and constants ============
User = get_user_model()
CODE = "mocked_code"
email_multi_class = "EmailMultiAlternatives"
generate_random_code = "generate_random_code"
actual_environment = os.environ.get("DJANGO_ENV", "development")


# =============== Fixtures ================
@pytest.fixture
def deactivated_user():
    """
    Fixture to create and return a deactivated User object.
    """
    return User.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fakeemail@email.com",
        password="FAKEpassword10!",
    )


# =============== Tests ================
@pytest.mark.skipif(
    actual_environment != "development",
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
@patch(f"{email_service_module_path}.{email_multi_class}")
@patch(f"{email_service_module_path}.{generate_random_code}", return_value=CODE)
def test_success_send_email_create_code_in_database(
    mock_generate_random_code: MagicMock,
    MockEmailMultiAlternatives: MagicMock,
    deactivated_user,
):
    # Returns a mocked instance of the EmailMultiAlternatives class
    mock_email_multi_instance = MockEmailMultiAlternatives.return_value

    send_reset_password_code_by_email(deactivated_user.email)

    mock_email_multi_instance.send.assert_called()

    assert ResetPasswordCodeModel.objects.filter(code=CODE).exists()
