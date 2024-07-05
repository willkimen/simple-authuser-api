from textwrap import dedent
from unittest.mock import MagicMock, mock_open, patch

import pytest
from django.contrib.auth import get_user_model

from user_app.utils.email_service import send_activation_email

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


@pytest.fixture
def mock_user():
    mock_user = MagicMock(spec_set=User)
    mock_user.id = 9999
    mock_user.email = "johndoe@email.com"
    mock_user.first_name = "John"
    mock_user.last_name = "Doe"
    mock_user.is_active = False
    mock_user.get_email_field_name.return_value = "email"
    return mock_user


@pytest.mark.django_db
@patch("user_app.utils.email_service.EmailMessage")
@patch("user_app.utils.email_service.generate_random_code", return_value="mocked-code")
@patch("user_app.utils.email_service.ConfirmationCode.objects.create")
def test_success_send_email(
    mock_create,
    mock_generate_random_code,
    MockEmailMessage,
    mock_user,
    expected_email_body,
):
    mock_email_message_instance = MockEmailMessage.return_value
    email_subject_expected = "Confirm your email address"

    send_activation_email(mock_user)

    MockEmailMessage.assert_called_once_with(
        subject=email_subject_expected, body=expected_email_body, to=[mock_user.email]
    )
    mock_email_message_instance.send.assert_called_once()
    mock_create.assert_called_once_with(
        confirmation_code=mock_generate_random_code(),
        user_email=mock_user.email,
        type_code="registration_email_confirmation",
    )
