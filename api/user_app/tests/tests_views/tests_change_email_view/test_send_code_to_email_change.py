import smtplib
from datetime import timedelta
from unittest.mock import MagicMock, patch

import jwt
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from user_app.constants import response_codes_and_messages
from user_app.models.code_models import ChangeEmailCodeModel
from user_app.tests.constants import (
    CHANGE_EMAIL_VIEW_MODULE_PATH,
    FAKE_SECRET,
    SEND_CHANGE_EMAIL_CODE_BY_EMAIL_FUNCTION_TO_PATCH,
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
url: str = reverse("send_code_to_email_change")
ACTUAL_LOGGED_USER_EMAIL = "loggeduser@email.com"
EMAIL_ALREADY_EXISTS = "emailalreadyexists@email.com"
NEW_EMAIL_1 = "newemail_1@email.com"
NEW_EMAIL_2 = "newemail_2@email.com"
OLD_CODE = "fake_old_code"


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


@pytest.fixture
def add_change_code_for_user(activated_user):
    """Insert a old code for actual user"""
    ChangeEmailCodeModel.objects.create(
        code=OLD_CODE, user=activated_user, new_email=NEW_EMAIL_1
    )


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
@patch(
    f"{CHANGE_EMAIL_VIEW_MODULE_PATH}.{SEND_CHANGE_EMAIL_CODE_BY_EMAIL_FUNCTION_TO_PATCH}",
    side_effect=smtplib.SMTPException(),
)
def test_do_not_send_code_if_email_sending_fails(
    send_email_change_code_by_email_function_mock: MagicMock,
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
        url, data={"email": NEW_EMAIL_1}, format="json"
    )

    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_status_code == actual_response.status_code


@pytest.mark.django_db
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_when_a_new_code_is_created_the_old_code_is_removed(
    client_auth_header: APIClient,
    add_change_code_for_user,
):
    """
    Tests the system behavior when creating a new change code.

    - An user already has an change code associated with their account.
    - When the client makes a POST request to the endpoint that sends the change
      code via email, a new code is generated.
    - The system should ensure that the old code is removed.

    Args:
      client_auth_header: API client used to simulate the POST request.
      add_change_code_for_user: Insert a old code for actual user
    """

    # Ensure that the old change code exists in the database before the request.
    assert ChangeEmailCodeModel.objects.filter(
        code=OLD_CODE, new_email=NEW_EMAIL_1
    ).exists()

    # Send a second email for change email
    client_auth_header.post(url, data={"email": NEW_EMAIL_2}, format="json")

    # After creating a new change code, verify that the old one has been removed.
    assert not ChangeEmailCodeModel.objects.filter(
        code=OLD_CODE, new_email=NEW_EMAIL_1
    ).exists()
    # Veryfy that exists new code.
    assert (
        ChangeEmailCodeModel.objects.filter(user_id=ACTUAL_LOGGED_USER_EMAIL).count()
        == 1
    )


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
        url, data={"email": NEW_EMAIL_1}, format="json"
    )

    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_status_code == actual_response.status_code
