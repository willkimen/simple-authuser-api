"""
Test the request_account_activation_code() view, which expects an account's email in a 
POST request and sends a activation code to the account's email address.
"""

from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from user_app.constants import http_response, validation_error_messages
from user_app.tests.constants import (
    ACTIVATE_ACCOUNT_VIEWS_MODULE_PATH,
    ALLOW_REQUEST_FUNCTION_TO_PATCH,
    Account,
)

# ========== Objects and constants ============
url: str = reverse("request_account_activation_code")
FAKE_ACCOUNT_DATA = {
    "first_name": "fake_first_name",
    "last_name": "fake_last_name",
    "email": "fake_email@email.com",
    "password": "FAKEpassowrd1234!",
}
EMAIL_NONEXISTENT = "nonexistent@email.com"


# ================= Fixtures ===============
@pytest.fixture
def active_account_email() -> str:
    """
    Fixture that creates an account with an activated account for testing purposes.

    This fixture creates a Account instance with an active account status. It returns
    the email address of the activated account.

    Returns:
        str: The email address of the account with the activated account.
    """

    return Account.objects.create_user(**FAKE_ACCOUNT_DATA, is_active=True).email


@pytest.fixture
def deactive_account_email() -> str:
    """
    Fixture that creates an account with a deactivated account for testing purposes.

    This fixture creates a Account instance with a deactivated account status (default).
    It returns the email address of the deactivated account.

    Returns:
        str: The email address of the account with the deactivated account.
    """

    return Account.objects.create_user(**FAKE_ACCOUNT_DATA, is_active=False).email


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
    f"{ACTIVATE_ACCOUNT_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
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
    expected_detail_message = http_response.VALIDATION_ERRORS["detail"]
    expected_code = http_response.VALIDATION_ERRORS["code"]

    actual_response = client.post(url, data={"email": ""}, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_error_message_field in actual_response.data["field_errors"]["email"]


@pytest.mark.django_db
@patch(
    f"{ACTIVATE_ACCOUNT_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
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
    expected_detail_message = http_response.VALIDATION_ERRORS["detail"]
    expected_code = http_response.VALIDATION_ERRORS["code"]

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
    f"{ACTIVATE_ACCOUNT_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
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
    expected_detail_message = http_response.VALIDATION_ERRORS["detail"]
    expected_code = http_response.VALIDATION_ERRORS["code"]

    actual_response = client.post(
        url, data={"email": invalid_email_format}, format="json"
    )

    assert expected_status_code == actual_response.status_code
    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_error_message_filed in actual_response.data["field_errors"]["email"]


@pytest.mark.django_db
@patch(
    f"{ACTIVATE_ACCOUNT_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_does_not_send_email_when_account_does_not_exists(
    allow_request_function_mock: MagicMock, client: APIClient
):
    """
    Test if the email sending request returns 404 when the account does not exist.

    Args:
        allow_request_function_mock (MagicMock): Mocked method to bypass rate limiting.
        client (APIClient): The API client used to make requests.

    This test checks that the server returns a 404 Not Found status code and
    an appropriate error message when the email field contains
    an email address that does not belong to any account.
    """
    expected_detail_message = http_response.ACCOUNT_NOT_FOUND["detail"]
    expected_code = http_response.ACCOUNT_NOT_FOUND["code"]
    expected_status_code = status.HTTP_404_NOT_FOUND

    actual_response = client.post(url, data={"email": EMAIL_NONEXISTENT}, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
@patch(
    f"{ACTIVATE_ACCOUNT_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_does_not_send_email_when_account_has_already_activated(
    allow_request_function_mock: MagicMock, client: APIClient, active_account_email: str
):
    """
    Test if the email sending request returns 400 when the account
    has already activated their account.

    Args:
        allow_request_function_mock (MagicMock): Mocked method to bypass rate limiting.
        client (APIClient): The API client used to make requests.
        active_account_email (str): The email address of the account with
                                 an activated account.

    This test checks that the server returns a 400 Bad Request status code and
    an appropriate error message when the email field contains an email address
    of an account who has already activated their account.
    """
    expected_detail_message = http_response.ACCOUNT_HAS_ALREADY_ACTIVATED["detail"]
    expected_code = http_response.ACCOUNT_HAS_ALREADY_ACTIVATED["code"]
    expected_status_code = status.HTTP_400_BAD_REQUEST

    actual_response = client.post(
        url, data={"email": active_account_email}, format="json"
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
@patch(
    f"{ACTIVATE_ACCOUNT_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_send_email_successfully(
    allow_request_function_mock: MagicMock,
    client: APIClient,
    deactive_account_email: str,
):
    """
    Test if the email sending request returns 200 when the email is sent successfully.

    Args:
        allow_request_function_mock (MagicMock): Mocked method to bypass rate limiting.
        client (APIClient): The API client used to make requests.
        deactive_account_email (str): The email address of the account with a
                                   deactivated account.

    This test checks that the server returns a 200 OK status code and an appropriate
    success message when the activation email is sent successfully.
    """
    expected_status_code = status.HTTP_200_OK
    expected_detail_message = http_response.EMAIL_SEND_TO_ACCOUNT_SUCCESSFULLY["detail"]
    expected_code = http_response.EMAIL_SEND_TO_ACCOUNT_SUCCESSFULLY["code"]

    actual_response = client.post(
        url, data={"email": deactive_account_email}, format="json"
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
