import smtplib
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from user_app.constants import response_messages

User = get_user_model()

url: str = reverse("send_email_to_activate_account")


@pytest.fixture
def client() -> APIClient:
    """Returns an API client to make requests."""

    return APIClient()


@pytest.fixture
def email_of_user_with_activated_account() -> str:
    """
    Fixture that creates a user with an activated account for testing purposes.

    This fixture creates a User instance with an active account status. It returns
    the email address of the activated user.

    Returns:
        str: The email address of the user with the activated account.
    """
    email = "johndoe@email.com"
    User.objects.create_user(
        first_name="John",
        last_name="Doe",
        email=email,
        password="Pass1234!",
        is_active=True,
    )

    return email


@pytest.fixture
def email_of_user_with_deactivated_account() -> str:
    """
    Fixture that creates a user with a deactivated account for testing purposes.

    This fixture creates a User instance with a deactivated account status (default).
    It returns the email address of the deactivated user.

    Returns:
        str: The email address of the user with the deactivated account.
    """
    email = "johndoe@email.com"
    user = User.objects.create_user(
        first_name="John",
        last_name="Doe",
        email=email,
        password="Pass1234!",
    )
    return email


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
    expected_message = "Request was throttled."
    expected_error_code = "throttled"
    limit_exceeded = 6

    # Simulate multiple POST requests to exceed the rate limit
    for _ in range(limit_exceeded):
        response = client.post(url)

    assert expected_status_code == response.status_code
    assert expected_message in response.data["message"]
    assert expected_error_code == response.data["error_code"]


@pytest.mark.django_db
@patch(
    "user_app.views.SendEmailActivateAccountRequestRateLimit.allow_request",
    return_value=True,
)
def test_does_not_send_email_when_email_field_is_empty(
    mock_allow_request, client: APIClient
):
    """
    Test if the email sending request returns 400 when the email field is empty.

    Args:
        mock_allow_request (MagicMock): Mocked method to bypass rate limiting.
        client (APIClient): The API client used to make requests.

    This test checks that the server returns a 400 Bad Request status code and an appropriate
    error message when the email field is empty in the request.
    """
    email_empty = {"email": ""}
    expected_message = "This field may not be blank."
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_field = "email"

    response = client.post(url, data=email_empty, format="json")

    assert expected_status_code == response.status_code
    assert expected_error_field in response.data["validation_errors"]
    assert expected_message in response.data["validation_errors"][expected_error_field]


@pytest.mark.django_db
@patch(
    "user_app.views.SendEmailActivateAccountRequestRateLimit.allow_request",
    return_value=True,
)
def test_does_not_send_email_when_email_field_is_null(
    mock_allow_request, client: APIClient
):
    """
    Test if the email sending request returns 400 when the email field is null.

    Args:
        mock_allow_request (MagicMock): Mocked method to bypass rate limiting.
        client (APIClient): The API client used to make requests.

    This test checks that the server returns a 400 Bad Request status code and an appropriate
    error message when the email field is null in the request.
    """
    email_null = {"email": None}
    expected_message = "This field may not be null."
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_field = "email"

    response = client.post(url, data=email_null, format="json")

    assert expected_status_code == response.status_code
    assert expected_error_field in response.data["validation_errors"]
    assert expected_message in response.data["validation_errors"][expected_error_field]


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
    "user_app.views.SendEmailActivateAccountRequestRateLimit.allow_request",
    return_value=True,
)
def test_does_not_send_email_with_invalid_email_format(
    mock_allow_request, invalid_email_format, client: APIClient
):
    """
    Test if the email sending request returns 400 when the email format is invalid.

    Args:
        mock_allow_request (MagicMock): Mocked method to bypass rate limiting.
        invalid_email_format (str): Invalid email format to test.
        client (APIClient): The API client used to make requests.

    This test checks that the server returns a 400 Bad Request status code and an appropriate
    error message when the email field contains an invalid email format.
    """
    email_with_invalid_format = {"email": invalid_email_format}
    expected_message = "Enter a valid email address."
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_field = "email"

    response = client.post(url, data=email_with_invalid_format, format="json")

    assert expected_status_code == response.status_code
    assert expected_error_field in response.data["validation_errors"]
    assert expected_message in response.data["validation_errors"][expected_error_field]


@pytest.mark.django_db
@patch(
    "user_app.views.SendEmailActivateAccountRequestRateLimit.allow_request",
    return_value=True,
)
def test_does_not_send_email_when_user_does_not_exists(
    mock_allow_request, client: APIClient
):
    """
    Test if the email sending request returns 404 when the user does not exist.

    Args:
        mock_allow_request (MagicMock): Mocked method to bypass rate limiting.
        client (APIClient): The API client used to make requests.

    This test checks that the server returns a 404 Not Found status code and an appropriate
    error message when the email field contains an email address that does not belong to any user.
    """
    expected_message = response_messages.USER_NOT_FOUND
    expected_status_code = status.HTTP_404_NOT_FOUND
    email_not_exist = {"email": "mynameisnobody@email.com"}

    response = client.post(url, data=email_not_exist, format="json")

    assert expected_status_code == response.status_code
    assert expected_message == response.data["message"]


@pytest.mark.django_db
@patch(
    "user_app.views.SendEmailActivateAccountRequestRateLimit.allow_request",
    return_value=True,
)
def test_does_not_send_email_when_user_has_already_activated(
    mock_allow_request, client: APIClient, email_of_user_with_activated_account: str
):
    """
    Test if the email sending request returns 400 when the user has already activated their account.

    Args:
        mock_allow_request (MagicMock): Mocked method to bypass rate limiting.
        client (APIClient): The API client used to make requests.
        email_of_user_with_activated_account (str): The email address of the user with an activated account.

    This test checks that the server returns a 400 Bad Request status code and an appropriate
    error message when the email field contains an email address of a user who has already activated their account.
    """
    expected_message = response_messages.USER_HAS_ALREADY_ACTIVATED
    expected_status_code = status.HTTP_400_BAD_REQUEST
    email_activated = {"email": email_of_user_with_activated_account}

    response = client.post(url, data=email_activated, format="json")

    assert expected_status_code == response.status_code
    assert expected_message == response.data["message"]


@pytest.mark.django_db
@patch(
    "user_app.views.SendEmailActivateAccountRequestRateLimit.allow_request",
    return_value=True,
)
@patch(
    "user_app.views.send_activation_code_by_email",
    side_effect=smtplib.SMTPException(),
)
def test_failed_to_send_email(
    mock_send_email,
    mock_allow_request,
    client: APIClient,
    email_of_user_with_deactivated_account: str,
):
    """
    Test if the email sending request returns 500 when there is an error sending the email.

    Args:
        mock_send_email (MagicMock): Mocked method to simulate an SMTP exception.
        mock_allow_request (MagicMock): Mocked method to bypass rate limiting.
        client (APIClient): The API client used to make requests.
        email_of_user_with_deactivated_account (str): The email address of the user with a deactivated account.

    This test checks that the server returns a 500 Internal Server Error status code and an appropriate
    error message when there is an SMTP exception while sending the activation email.
    """
    expected_message = response_messages.ERROR_SENDING_EMAIL
    expected_status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    response = client.post(
        url, data={"email": email_of_user_with_deactivated_account}, format="json"
    )

    assert expected_status_code == response.status_code
    assert expected_message == response.data["message"]


@pytest.mark.django_db
@patch(
    "user_app.views.SendEmailActivateAccountRequestRateLimit.allow_request",
    return_value=True,
)
@patch("user_app.views.send_activation_code_by_email")
def test_send_email_successfully(
    mock_send_email,
    mock_allow_request,
    client: APIClient,
    email_of_user_with_deactivated_account: str,
):
    """
    Test if the email sending request returns 200 when the email is sent successfully.

    Args:
        mock_send_email (MagicMock): Mocked method to simulate successful email sending.
        mock_allow_request (MagicMock): Mocked method to bypass rate limiting.
        client (APIClient): The API client used to make requests.
        email_of_user_with_deactivated_account (str): The email address of the user with a deactivated account.

    This test checks that the server returns a 200 OK status code and an appropriate
    success message when the activation email is sent successfully.
    """
    expected_status_code = status.HTTP_200_OK
    expected_message = response_messages.EMAIL_SEND_TO_USER_SUCCESSFULLY

    response = client.post(
        url, data={"email": email_of_user_with_deactivated_account}, format="json"
    )

    assert expected_status_code == response.status_code
    assert expected_message == response.data["message"]
