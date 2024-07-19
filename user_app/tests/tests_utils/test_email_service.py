from textwrap import dedent
from unittest.mock import MagicMock, mock_open, patch

import pytest
from django.contrib.auth import get_user_model

from user_app.utils.email_service import send_activation_code_by_email

User = get_user_model()


@pytest.fixture
def expected_email_body():
    return dedent(
        """
    Your confirmation code is below - enter it in your open browser window and we'll help you to sign in.

    mocked-code

    If you haven't requested this email, there's nothing to worry about - you can safely ignore it.
    """
    )


@pytest.mark.django_db
@patch("user_app.utils.email_service.EmailMessage")
@patch("user_app.utils.email_service.generate_random_code", return_value="mocked-code")
@patch("user_app.utils.email_service.ConfirmationCode.objects.create")
@patch(
    "user_app.utils.email_service.ConfirmationCode.objects.exists", return_value=False
)
def test_success_send_email(
    mock_exists,
    mock_create,
    mock_generate_random_code,
    MockEmailMessage,
    expected_email_body,
):
    user_email = "johndoe@email.com"
    mock_email_message_instance = MockEmailMessage.return_value
    email_subject_expected = "Confirm your email address"

    send_activation_code_by_email(user_email)

    MockEmailMessage.assert_called_once_with(
        subject=email_subject_expected, body=expected_email_body, to=[user_email]
    )
    mock_email_message_instance.send.assert_called_once()
    mock_create.assert_called_once_with(
        code=mock_generate_random_code(),
        user_email=user_email,
        type_code="registration_email_confirmation",
    )
