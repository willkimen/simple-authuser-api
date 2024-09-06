"""
This module tests the function for sending an email with an account confirmation code.
"""

from textwrap import dedent
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model

from user_app.constants.path_for_mock import email_service_module_path
from user_app.utils.email_service import send_activation_code_by_email

# ========== Objects and constants ============
User = get_user_model()
FAKE_USER_EMAIL = "fake@email.com"
FAKE_CODE = "mocked_code"
email_message_path_for_mock = "EmailMessage"
generate_random_code_path_for_mock = "generate_random_code"
create_path_for_mock = "AccountActivationCodeModel.objects.create"
exists_path_for_mock = "AccountActivationCodeModel.objects.exists"


# =============== Fixture =================
@pytest.fixture
def expected_email_body():
    return dedent(
        """
    Your confirmation code is below - enter it in your open browser window and we'll help you to sign in.

    mocked_code

    If you haven't requested this email, there's nothing to worry about - you can safely ignore it.
    """
    )


# =============== Tests ================
@pytest.mark.django_db
@patch(f"{email_service_module_path}.{email_message_path_for_mock}")
@patch(
    f"{email_service_module_path}.{generate_random_code_path_for_mock}",
    return_value="mocked_code",
)
@patch(f"{email_service_module_path}.{create_path_for_mock}")
@patch(f"{email_service_module_path}.{exists_path_for_mock}", return_value=False)
def test_success_send_email(
    mock_exists: MagicMock,
    mock_create: MagicMock,
    mock_generate_random_code: MagicMock,
    MockEmailMessage: MagicMock,
    expected_email_body: str,
):
    user_email = FAKE_USER_EMAIL
    # Returns a mocked instance of the EmailMessage class
    mock_email_message_instance = MockEmailMessage.return_value
    email_subject_expected = "Confirm your email address"

    send_activation_code_by_email(user_email)

    MockEmailMessage.assert_called_once_with(
        subject=email_subject_expected, body=expected_email_body, to=[user_email]
    )
    mock_email_message_instance.send.assert_called_once()
    mock_create.assert_called_once_with(
        code=FAKE_CODE,
        user_email=user_email,
    )
