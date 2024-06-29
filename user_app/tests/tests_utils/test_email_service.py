from textwrap import dedent
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model

from user_app.utils.email_service import send_activation_email

User = get_user_model()


@pytest.fixture
def expected_email_body():
    return dedent(
        """
    Hi John Doe,

    Please click the link below to activate your account:

    http://mocked-domain/api/v1/users/confirmation_register/mocked-uid/mocked-token/

    If you did not request this email, please ignore it.
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


@patch("user_app.utils.email_service.EmailMessage")
@patch("user_app.utils.email_service.os.environ.get")
@patch("user_app.utils.email_service.user_active_generate_token.make_token")
@patch("user_app.utils.email_service.urlsafe_base64_encode")
def test_success_send_email(
    mock_encode,
    mock_make_token,
    mock_environ_domain,
    MockEmailMessage,
    mock_user,
    expected_email_body,
):
    mock_encode.return_value = "mocked-uid"
    mock_make_token.return_value = "mocked-token"
    mock_environ_domain.return_value = "mocked-domain"
    mock_email_message_instance = MockEmailMessage.return_value
    email_subject_expected = "Activate your account"

    send_activation_email(mock_user)

    MockEmailMessage.assert_called_once_with(
        subject=email_subject_expected, body=expected_email_body, to=[mock_user.email]
    )
    # Verify if the email send
    mock_email_message_instance.send.assert_called_once()
