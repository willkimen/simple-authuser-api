import smtplib
from datetime import timedelta
from unittest.mock import MagicMock, patch

import jwt
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from user_app.constants import response_codes_and_messages
from user_app.constants.path_for_mock import (
    change_email_view_path,
    token_utils_module_path,
)

# =========== Objects and constants ==============
User = get_user_model()
url: str = reverse("send_code_to_email_change")
SECRET = "token_secret"
LOGGED_USER_EMAIL = "loggeduser@email.com"
EMAIL_ALREADY_EXISTS = "emailalreadyexists@email.com"
os_environ_get = "os.environ.get"
send_change_email_code_by_email = "send_change_email_code_by_email"


# ============ Fixtures ================
@pytest.fixture
def activated_user() -> User:
    """
    Provides a user object that is persisted in the database.
    """
    return User.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email=LOGGED_USER_EMAIL,
        password="FAKEpassword10!",
        is_active=True,
    )


@pytest.fixture
def client_auth_header(activated_user) -> APIClient:
    """
    Provides an API client with JWT authentication in the request header.

    Returns:
        APIClient: An API client with the Authorization header set to a valid JWT token.
    """
    token = jwt.encode(
        {
            "uid": activated_user.id,
            "typ": "access",
            "jti": "fake_jti",
            "exp": int((timezone.now() + timedelta(seconds=60)).timestamp()),
        },
        SECRET,
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


# ============ Tests ================
@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
def test_do_not_send_code_if_email_is_same_as_logged_in_user(
    token_secret_mock: MagicMock,
    client_auth_header: APIClient,
):
    """
    Tests the scenario where the new email provided by the user is the
    same as the email of the logged-in user.
    """
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_code = response_codes_and_messages.EMAIL_ALREADY_IN_USE["code"]
    expected_detail_message = response_codes_and_messages.EMAIL_ALREADY_IN_USE["detail"]

    actual_response = client_auth_header.post(
        url, data={"email": LOGGED_USER_EMAIL}, format="json"
    )

    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_status_code == actual_response.status_code


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
def test_do_not_send_code_if_email_already_exists_in_database(
    token_secret_mock: MagicMock,
    client_auth_header: APIClient,
):
    """
    Tests the scenario where the new email provided by the user already
    exists in the system.
    """
    # Create a user to have an email in the database that already exists
    User.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email=EMAIL_ALREADY_EXISTS,
        password="FAKEpassword10!",
        is_active=True,
    )

    expected_status_code = status.HTTP_409_CONFLICT
    expected_code = response_codes_and_messages.EMAIL_ALREADY_EXISTS["code"]
    expected_detail_message = response_codes_and_messages.EMAIL_ALREADY_EXISTS["detail"]

    actual_response = client_auth_header.post(
        url, data={"email": EMAIL_ALREADY_EXISTS}, format="json"
    )

    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_status_code == actual_response.status_code


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
@patch(
    f"{change_email_view_path}.{send_change_email_code_by_email}",
    side_effect=smtplib.SMTPException(),
)
def test_do_not_send_code_if_email_sending_fails(
    token_secret_mock: MagicMock,
    send_email_mock: MagicMock,
    client_auth_header: APIClient,
):
    """
    Tests the scenario where sending the confirmation email fails.
    The system attempts to send the confirmation email, but an SMTP exception occurs.
    """
    expected_status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    expected_code = response_codes_and_messages.ERROR_SENDING_EMAIL["code"]
    expected_detail_message = response_codes_and_messages.ERROR_SENDING_EMAIL["detail"]

    actual_response = client_auth_header.post(
        url, data={"email": "fake_email@email.com"}, format="json"
    )

    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_status_code == actual_response.status_code


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
def test_send_code_successfully(
    token_secret_mock: MagicMock,
    client_auth_header: APIClient,
):
    """
    Tests the successful case of sending the confirmation email to
    the new email address.
    The user provides a valid new email that is not registered to any other account.
    """
    expected_status_code = status.HTTP_200_OK
    expected_code = response_codes_and_messages.EMAIL_SEND_TO_USER_SUCCESSFULLY["code"]
    expected_detail_message = response_codes_and_messages.EMAIL_SEND_TO_USER_SUCCESSFULLY[
        "detail"
    ]

    actual_response = client_auth_header.post(
        url, data={"email": "fake_email@email.com"}, format="json"
    )

    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_status_code == actual_response.status_code
