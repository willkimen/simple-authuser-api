import smtplib
from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from user_app.constants import response_codes_and_messages
from user_app.tests.constants import (
    ALLOW_REQUEST_FUNCTION_TO_PATCH,
    RESET_PASSWORD_VIEW_MODULE_PATH,
    SEND_RESET_PASSWORD_CODE_BY_EMAIL_FUNCTION_TO_PATCH,
    User,
)

# =========== Objects and constants ==============
url: str = reverse("send_code_to_reset_password")
USER_EMAIL = "fakeemail@email.com"
NON_EXISTENT_EMAIL = "nonexistent@email.com"


# ============ Fixtures ================
@pytest.fixture
def deactivate_user():
    """
    Fixture to create and return a deactivated User object.
    """
    return User.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email=USER_EMAIL,
        password="1234@!AA",
        is_active=False,
    )


@pytest.fixture
def activate_user():
    """
    Fixture to create and return an activated User object.
    """
    return User.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email=USER_EMAIL,
        password="1234@!AA",
        is_active=True,
    )


# ============ Tests ================
@pytest.mark.django_db
@patch(
    f"{RESET_PASSWORD_VIEW_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_does_not_send_code_when_non_existent_email_in_database(
    allow_request_function_mock: MagicMock, client: APIClient
):
    """
    Tests that the system does not send a password reset code when the provided email
    is not found in the database.
    """
    expected_detail_message = response_codes_and_messages.USER_NOT_FOUND["detail"]
    expected_code = response_codes_and_messages.USER_NOT_FOUND["code"]
    expected_status_code = status.HTTP_404_NOT_FOUND

    actual_response = client.post(
        url, data={"email": NON_EXISTENT_EMAIL}, format="json"
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
@patch(
    f"{RESET_PASSWORD_VIEW_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_does_not_send_code_when_deactivate_user(
    allow_request_function_mock: MagicMock, client: APIClient, deactivate_user
):
    """
    Tests that the system does not send a password reset code when the user's account is
    deactivated.
    """
    expected_detail_message = response_codes_and_messages.USER_ACCOUNT_NOT_ACTIVATED[
        "detail"
    ]
    expected_code = response_codes_and_messages.USER_ACCOUNT_NOT_ACTIVATED["code"]
    expected_status_code = status.HTTP_403_FORBIDDEN

    actual_response = client.post(
        url, data={"email": deactivate_user.email}, format="json"
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
@patch(
    f"{RESET_PASSWORD_VIEW_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
@patch(
    f"{RESET_PASSWORD_VIEW_MODULE_PATH}.{SEND_RESET_PASSWORD_CODE_BY_EMAIL_FUNCTION_TO_PATCH}",
    side_effect=smtplib.SMTPException(),
)
def test_does_not_send_code_when_failed_to_send_email(
    send_code_function_mock: MagicMock,
    allow_request_function_mock: MagicMock,
    client: APIClient,
    activate_user,
):
    """
    Tests that the system does not send a password reset code when there is an error
    sending the email (e.g., SMTPException).
    """
    expected_detail_message = response_codes_and_messages.ERROR_SENDING_EMAIL["detail"]
    expected_code = response_codes_and_messages.ERROR_SENDING_EMAIL["code"]
    expected_status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    actual_response = client.post(
        url, data={"email": activate_user.email}, format="json"
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
def test_does_not_send_code_when_request_limit_is_reached(client: APIClient):
    """
    Tests that the system prevents sending the password reset code when the request rate
    limit has been reached.
    """
    expected_status_code = status.HTTP_429_TOO_MANY_REQUESTS
    expected_detail_message = "Request was throttled."
    expected_code = "throttled"
    limit_exceeded = 6

    # Simulate multiple POST requests to exceed the rate limit
    for _ in range(limit_exceeded):
        actual_response = client.post(url)

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message in actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
@patch(
    f"{RESET_PASSWORD_VIEW_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_sends_the_code_to_the_user_email_successfully(
    allow_request_function_mock: MagicMock, client: APIClient, activate_user
):
    """
    Tests that the system successfully sends the password reset code to the user's email
    when the user is found and active.
    """
    expected_detail_message = (
        response_codes_and_messages.EMAIL_SEND_TO_USER_SUCCESSFULLY["detail"]
    )
    expected_code = response_codes_and_messages.EMAIL_SEND_TO_USER_SUCCESSFULLY["code"]
    expected_status_code = status.HTTP_200_OK

    actual_response = client.post(
        url, data={"email": activate_user.email}, format="json"
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
