from datetime import timedelta
from unittest.mock import patch

import jwt
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from user_app.constants import response_codes_and_messages
from user_app.tests.constants import (
    FAKE_SECRET,
    TOKEN_SECRET_SETTING_TO_PATCH,
    TOKEN_UTILS_MODULE_PATH,
    User,
)

# =========== Objects and constants ==============
FAKE_USER_DATA = {
    "first_name": "fake_first_name",
    "last_name": "fake_last_name",
    "password": "FAKEpassowrd1234!",
    "is_active": True,
}
url: str = reverse("request_email_change_code")
ACTUAL_LOGGED_USER_EMAIL = "loggeduser@email.com"
EMAIL_ALREADY_EXISTS = "emailalreadyexists@email.com"
NEW_EMAIL = "newemail@email.com"


# ============ Fixtures ================
@pytest.fixture
def activated_user():
    """
    Provides a user object that is persisted in the database.
    """
    return User.objects.create_user(**FAKE_USER_DATA, email=ACTUAL_LOGGED_USER_EMAIL)


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
        FAKE_SECRET,
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


# ============ Tests ================
@pytest.mark.django_db
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_do_not_send_code_if_email_is_same_as_logged_in_user(
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
        url, data={"email": ACTUAL_LOGGED_USER_EMAIL}, format="json"
    )

    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_status_code == actual_response.status_code


@pytest.mark.django_db
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_do_not_send_code_if_email_already_exists_in_database(
    client_auth_header: APIClient,
):
    """
    Tests the scenario where the new email provided by the user already
    exists in the system.
    """
    # Create a user to have an email in the database that already exists
    User.objects.create_user(**FAKE_USER_DATA, email=EMAIL_ALREADY_EXISTS)

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
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_send_code_successfully(client_auth_header: APIClient):
    """
    Tests the successful case of sending the confirmation email to
    the new email address.
    The user provides a valid new email that is not registered to any other account.
    """
    expected_status_code = status.HTTP_200_OK
    expected_code = response_codes_and_messages.EMAIL_SEND_TO_USER_SUCCESSFULLY["code"]
    expected_detail_message = (
        response_codes_and_messages.EMAIL_SEND_TO_USER_SUCCESSFULLY["detail"]
    )

    actual_response = client_auth_header.post(
        url, data={"email": NEW_EMAIL}, format="json"
    )

    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_status_code == actual_response.status_code
