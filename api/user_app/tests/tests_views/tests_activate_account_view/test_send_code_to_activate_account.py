"""
Test the send_code_to_activate_account() view, which expects a user's email in a 
POST request and sends a confirmation code to the user's email address.
"""

import smtplib
from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from user_app.constants import response_codes_and_messages, validation_error_messages
from user_app.tests.constants import (
    ACTIVATE_ACCOUNT_VIEW_MODULE_PATH,
    ALLOW_REQUEST_FUNCTION_TO_PATCH,
    SEND_ACTIVATION_CODE_BY_EMAIL_FUNCTION_TO_PATCH,
    User,
)

# ========== Objects and constants ============
url: str = reverse("send_code_to_activate_account")
FAKE_USER_DATA = {
    "first_name": "fake_first_name",
    "last_name": "fake_last_name",
    "email": "fake_email@email.com",
    "password": "FAKEpassowrd1234!",
}
EMAIL_NONEXISTENT = "nonexistent@email.com"


# ================= Fixtures ===============
@pytest.fixture
def active_user_email() -> str:
    """
    Fixture that creates a user with an activated account for testing purposes.

    This fixture creates a User instance with an active account status. It returns
    the email address of the activated user.

    Returns:
        str: The email address of the user with the activated account.
    """

    return User.objects.create_user(**FAKE_USER_DATA, is_active=True).email


@pytest.fixture
def deactive_user_email() -> str:
    """
    Fixture that creates a user with a deactivated account for testing purposes.

    This fixture creates a User instance with a deactivated account status (default).
    It returns the email address of the deactivated user.

    Returns:
        str: The email address of the user with the deactivated account.
    """

    return User.objects.create_user(**FAKE_USER_DATA, is_active=False).email


# ============= Tests ==================
@pytest.mark.django_db
def test_does_not_send_email_when_request_limit_is_reached(client: APIClient):
    """
    Test if the send email for account activation request is throttled when the request limit is reached.

    Args:
        client (APIClient): The API client used to make requests.

    This test ensures that the server returns a 429 Too Many Requests status code
    and the appropriate error message when the rate limit requests is exceeded.
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
    f"{ACTIVATE_ACCOUNT_VIEW_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_does_not_send_email_when_email_field_is_empty(
    allow_request_function_mock: MagicMock, client: APIClient
):
    """
    Test if the email sending request returns 400 when the email field is empty.

    Args:
        allow_request_function_mock (MagicMock): Mocked method to bypass rate limiting.
        client (APIClient): The API client used to make requests.

    This test checks that the server returns a 400 Bad Request status code and
    an appropriate error message when the email field is empty in the request.
    """

    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_message_field = validation_error_messages.BLANK_FIELD
    expected_detail_message = response_codes_and_messages.VALIDATION_ERRORS["detail"]
    expected_code = response_codes_and_messages.VALIDATION_ERRORS["code"]

    actual_response = client.post(url, data={"email": ""}, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_error_message_field in actual_response.data["field_errors"]["email"]


@pytest.mark.django_db
@patch(
    f"{ACTIVATE_ACCOUNT_VIEW_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_does_not_send_email_when_email_field_is_null(
    allow_request_function_mock: MagicMock, client: APIClient
):
    """
    Test if the email sending request returns 400 when the email field is null.

    Args:
        allow_request_function_mock (MagicMock): Mocked method to bypass rate limiting.
        client (APIClient): The API client used to make requests.

    This test checks that the server returns a 400 Bad Request status code and
    an appropriate error message when the email field is null in the request.
    """
    expected_error_message_field = validation_error_messages.NULL_FIELD
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_detail_message = response_codes_and_messages.VALIDATION_ERRORS["detail"]
    expected_code = response_codes_and_messages.VALIDATION_ERRORS["code"]

    actual_response = client.post(url, data={"email": None}, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_error_message_field in actual_response.data["field_errors"]["email"]


@pytest.mark.parametrize(
    "invalid_email_format",
    [
        "email.com",
        "email@@domain.com",
        ".email@domain.com",
        "email.@domain.com",
        "em..ail@domain.com",
        "e mail@domain.com",
        "@domain.com",
        "email@",
        "email@domain",
        "email@domain..com",
        "email@[domain.com]",
        "email@domain.",
    ],
)
@pytest.mark.django_db
@patch(
    f"{ACTIVATE_ACCOUNT_VIEW_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_does_not_send_email_with_invalid_email_format(
    allow_request_function_mock: MagicMock, invalid_email_format, client: APIClient
):
    """
    Test if the email sending request returns 400 when the email format is invalid.

    Args:
        allow_request_function_mock (MagicMock): Mocked method to bypass rate limiting.
        invalid_email_format (str): Invalid email format to test.
        client (APIClient): The API client used to make requests.

    This test checks that the server returns a 400 Bad Request status code and
    an appropriate error message when the email field contains an invalid email format.
    """
    expected_error_message_filed = validation_error_messages.INVALID_FORMAT_EMAIL
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_detail_message = response_codes_and_messages.VALIDATION_ERRORS["detail"]
    expected_code = response_codes_and_messages.VALIDATION_ERRORS["code"]

    actual_response = client.post(
        url, data={"email": invalid_email_format}, format="json"
    )

    assert expected_status_code == actual_response.status_code
    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_error_message_filed in actual_response.data["field_errors"]["email"]


@pytest.mark.django_db
@patch(
    f"{ACTIVATE_ACCOUNT_VIEW_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_does_not_send_email_when_user_does_not_exists(
    allow_request_function_mock: MagicMock, client: APIClient
):
    """
    Test if the email sending request returns 404 when the user does not exist.

    Args:
        allow_request_function_mock (MagicMock): Mocked method to bypass rate limiting.
        client (APIClient): The API client used to make requests.

    This test checks that the server returns a 404 Not Found status code and
    an appropriate error message when the email field contains
    an email address that does not belong to any user.
    """
    expected_detail_message = response_codes_and_messages.USER_NOT_FOUND["detail"]
    expected_code = response_codes_and_messages.USER_NOT_FOUND["code"]
    expected_status_code = status.HTTP_404_NOT_FOUND

    actual_response = client.post(url, data={"email": EMAIL_NONEXISTENT}, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
@patch(
    f"{ACTIVATE_ACCOUNT_VIEW_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_does_not_send_email_when_user_has_already_activated(
    allow_request_function_mock: MagicMock, client: APIClient, active_user_email: str
):
    """
    Test if the email sending request returns 400 when the user
    has already activated their account.

    Args:
        allow_request_function_mock (MagicMock): Mocked method to bypass rate limiting.
        client (APIClient): The API client used to make requests.
        active_user_email (str): The email address of the user with
                                 an activated account.

    This test checks that the server returns a 400 Bad Request status code and
    an appropriate error message when the email field contains an email address
    of a user who has already activated their account.
    """
    expected_detail_message = response_codes_and_messages.USER_HAS_ALREADY_ACTIVATED[
        "detail"
    ]
    expected_code = response_codes_and_messages.USER_HAS_ALREADY_ACTIVATED["code"]
    expected_status_code = status.HTTP_400_BAD_REQUEST

    actual_response = client.post(url, data={"email": active_user_email}, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
@patch(
    f"{ACTIVATE_ACCOUNT_VIEW_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
@patch(
    f"{ACTIVATE_ACCOUNT_VIEW_MODULE_PATH}.{SEND_ACTIVATION_CODE_BY_EMAIL_FUNCTION_TO_PATCH}",
    side_effect=smtplib.SMTPException(),
)
def test_failed_to_send_email(
    send_email_function_mock: MagicMock,
    allow_request_function_mock: MagicMock,
    client: APIClient,
    deactive_user_email: str,
):
    """
    Test if the email sending request returns 500 when there is
    an error sending the email.

    Args:
        send_email_function_mock (MagicMock): Mocked method to simulate an
                                              SMTP exception.
        allow_request_function_mock (MagicMock): Mocked method to bypass rate limiting.
        client (APIClient): The API client used to make requests.
        deactive_user_email (str): The email address of the user with
                                   a deactivated account.

    This test checks that the server returns a 500 Internal Server Error status code
    and an appropriate error message when there is an SMTP exception while sending
    the activation email.
    """
    expected_detail_message = response_codes_and_messages.ERROR_SENDING_EMAIL["detail"]
    expected_code = response_codes_and_messages.ERROR_SENDING_EMAIL["code"]
    expected_status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    actual_response = client.post(
        url, data={"email": deactive_user_email}, format="json"
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
@patch(
    f"{ACTIVATE_ACCOUNT_VIEW_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_send_email_successfully(
    allow_request_function_mock: MagicMock,
    client: APIClient,
    deactive_user_email: str,
):
    """
    Test if the email sending request returns 200 when the email is sent successfully.

    Args:
        allow_request_function_mock (MagicMock): Mocked method to bypass rate limiting.
        client (APIClient): The API client used to make requests.
        deactive_user_email (str): The email address of the user with a
                                   deactivated account.

    This test checks that the server returns a 200 OK status code and an appropriate
    success message when the activation email is sent successfully.
    """
    expected_status_code = status.HTTP_200_OK
    expected_detail_message = (
        response_codes_and_messages.EMAIL_SEND_TO_USER_SUCCESSFULLY["detail"]
    )
    expected_code = response_codes_and_messages.EMAIL_SEND_TO_USER_SUCCESSFULLY["code"]

    actual_response = client.post(
        url, data={"email": deactive_user_email}, format="json"
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
