from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.timezone import make_aware
from rest_framework import status
from rest_framework.test import APIClient

from user_app.constants import confirmation_type_code, response_messages
from user_app.models import ConfirmationCode

User = get_user_model()

url: str = reverse("activate_account")


@pytest.fixture
def client() -> APIClient:
    """Returns an API client to make requests."""

    return APIClient()


@pytest.fixture
def incorrect_type_code() -> str:
    """
    This fixture creates a ConfirmationCode instance with a type code that does not match
     the type expected for account activation.
    """
    incorrect_type = confirmation_type_code.PASSWORD_RESET
    confirmation_code = ConfirmationCode.objects.create(
        user_email="jhonDoe@email.com",
        code="example-code",
        type_code=incorrect_type,
    )

    return confirmation_code.code


@pytest.fixture
def expired_code() -> str:
    """
    Creates a ConfirmationCode instance with an expired date (24h + 1 minute ago compared to now)
    """
    now = make_aware(datetime.now())
    expired_date = now.replace(day=now.day - 1, second=now.second - 1)

    confirmation_code = ConfirmationCode.objects.create(
        user_email="jhonDoe@email.com",
        code="example-code",
        type_code=confirmation_type_code.ACCOUNT_ACTIVATION,
    )

    confirmation_code.created_at = expired_date
    confirmation_code.save()

    return confirmation_code.code


@pytest.fixture
def user_id_and_code() -> dict:
    """
    Fixture that creates a user and a confirmation code for testing purposes.

    This fixture creates a User instance and a related ConfirmationCode instance
    for account activation. It returns a dictionary containing the user's ID and
    the confirmation code.

    Returns:
        dict: A dictionary with the user's ID and the confirmation code.
    """
    user = User.objects.create(
        first_name="John",
        last_name="Doe",
        email="johndoe@email.com",
        password="Password1234!",
    )

    confirmation_code = ConfirmationCode.objects.create(
        user_email=user.email,
        type_code=confirmation_type_code.ACCOUNT_ACTIVATION,
        code="fake_code",
    )

    return {"user_id": user.id, "code": confirmation_code.code}


@pytest.mark.django_db
@patch(
    "user_app.views.AccountActivationRequestRateLimit.allow_request", return_value=True
)
def test_successful_account_activation(
    mock_allow_request: MagicMock, user_id_and_code: dict, client: APIClient
):
    """
    Test if the account activation request successfully activates the account.

    Args:
        mock_allow_request (MagicMock): Mocked method to bypass rate limiting.
        user_id_and_code (dict): A dictionary with the user's ID and the confirmation code.
        client (APIClient): The API client used to make requests.

    This test checks that the server returns a 200 OK status code and an appropriate
    success message when a valid activation code is provided. It also verifies that
    the user's account is activated.
    """
    expected_message = response_messages.ACCOUNT_ACTIVATED
    expected_status_code = status.HTTP_200_OK

    response = client.post(url, data={"code": user_id_and_code["code"]}, format="json")

    assert expected_status_code == response.status_code
    assert expected_message == response.data["message"]

    # Verify that the user's account is activated
    user = User.objects.get(id=user_id_and_code["user_id"])
    assert user.is_active == True


@pytest.mark.django_db
@patch(
    "user_app.views.AccountActivationRequestRateLimit.allow_request", return_value=True
)
def test_successfully_activated_account_removes_the_code_in_the_database(
    mock_allow_request: MagicMock, user_id_and_code: dict, client: APIClient
):
    """
    Test if the confirmation code is removed from the database after successful activation.

    Args:
        mock_allow_request (MagicMock): Mocked method to bypass rate limiting.
        user_id_and_code (dict): A dictionary with the user's ID and the confirmation code.
        client (APIClient): The API client used to make requests.

    This test checks that the confirmation code is deleted from the database
    after a successful account activation.
    """
    response = client.post(url, data={"code": user_id_and_code["code"]}, format="json")

    # Assert that the confirmation code no longer exists in the database
    assert not ConfirmationCode.objects.filter(code=user_id_and_code["code"]).exists()


@pytest.mark.django_db
@patch(
    "user_app.views.AccountActivationRequestRateLimit.allow_request", return_value=True
)
def test_not_activate_account_when_expired_code(
    mock_allow_request: MagicMock,
    expired_code: str,
    client: APIClient,
):
    """
    Test if the account activation request returns 410 when the provided code is expired.

    Args:
        mock_throttle_classes (MagicMock): Mocked throttle classes to bypass rate limiting.
        expired_code (str): The expired confirmation code.
        client (APIClient): The API client used to make requests.

    This test checks that the server returns a 410 Gone status code and an appropriate
    error message when an expired activation code is provided in the request.
    """
    expected_message = response_messages.CODE_EXPIRED
    expected_status_code = status.HTTP_410_GONE

    response = client.post(url, data={"code": expired_code}, format="json")

    assert expected_status_code == response.status_code
    assert expected_message == response.data["message"]


@pytest.mark.django_db
@patch(
    "user_app.views.AccountActivationRequestRateLimit.allow_request", return_value=True
)
def test_expired_code_is_removed_from_the_database(
    mock_allow_request: MagicMock,
    expired_code: str,
    client: APIClient,
):
    """
    Test if the expired code is removed from the database when verified that it is expired.

    Args:
        mock_throttle_classes (MagicMock): Mocked throttle classes to bypass rate limiting.
        expired_code (str): The expired confirmation code.
        client (APIClient): The API client used to make requests.

    This test checks that an expired confirmation code is deleted from the database
    after an account activation attempt with the expired code.
    """
    client.post(url, data={"code": expired_code}, format="json")

    # Assert that the expired code no longer exists in the database
    assert not ConfirmationCode.objects.filter(code=expired_code).exists()


@pytest.mark.django_db
@patch(
    "user_app.views.AccountActivationRequestRateLimit.allow_request", return_value=True
)
def test_not_activate_account_when_code_field_does_not_exists(
    mock_allow_request: MagicMock, client: APIClient
):
    """
    Test if the account activation request returns 404 when the provided code does not exist.

    Args:
        mock_throttle_classes (MagicMock): Mocked throttle classes to bypass rate limiting.
        client (APIClient): The API client used to make requests.

    This test checks that the server returns a 404 Not Found status code and an appropriate
    error message when a non-existent activation code is provided in the request.
    """
    code_not_exists = "example-code"
    expected_message = response_messages.ACCOUNT_ACTIVATION_CODE_NOT_FOUND
    expected_status_code = status.HTTP_404_NOT_FOUND

    response = client.post(url, data={"code": code_not_exists}, format="json")

    assert expected_status_code == response.status_code
    assert expected_message == response.data["message"]


@pytest.mark.django_db
@patch(
    "user_app.views.AccountActivationRequestRateLimit.allow_request", return_value=True
)
@pytest.mark.parametrize("wrong_field_name", ["cod", ""])
def test_code_field_is_required(
    mock_allow_request: MagicMock,
    wrong_field_name: str,
    client: APIClient,
):
    """
    Test if the account activation request returns 400 when the 'code' field is missing or incorrect.

    Args:
        mock_throttle_classes (MagicMock): Mocked throttle classes to bypass rate limiting.
        wrong_field_name (str): The incorrect or missing field name to test.
        client (APIClient): The API client used to make requests.

    This test checks that the server returns a 400 Bad Request status code and an appropriate
    error message when the 'code' field is missing or incorrectly named in the request.
    """
    code = "example-code"
    expected_message = response_messages.CODE_FIELD_IS_REQUIRED
    expected_status_code = status.HTTP_400_BAD_REQUEST

    response = client.post(url, data={wrong_field_name: code}, format="json")

    assert expected_status_code == response.status_code
    assert expected_message == response.data["message"]


@pytest.mark.django_db
@patch(
    "user_app.views.AccountActivationRequestRateLimit.allow_request", return_value=True
)
def test_not_activate_account_when_code_type_is_incorrect(
    mock_allow_request: MagicMock,
    client: APIClient,
    incorrect_type_code: str,
):
    """
    Test if the account activation request returns 400 when the type of the provided code is incorrect.

    Args:
        mock_throttle_classes (MagicMock): Mocked throttle classes to bypass rate limiting.
        client (APIClient): The API client used to make requests.
        incorrect_type_code (str): The confirmation code with an incorrect type.

    This test checks that the server returns a 400 Bad Request status code and an appropriate
    error message when the type of the provided activation code is incorrect.
    """
    expected_message = response_messages.INVALID_CONFIRMATION_CODE_TYPE
    expected_status_code = status.HTTP_400_BAD_REQUEST

    response = client.post(url, data={"code": incorrect_type_code}, format="json")

    assert expected_status_code == response.status_code
    assert expected_message == response.data["message"]


# Leave it for last to avoid any problems regarding the request rate limit
@pytest.mark.django_db
def test_not_activate_account_when_request_limit_is_reached(client: APIClient):
    """
    Test if the account activation request is throttled when the request limit is reached.

    Args:
        client (APIClient): The API client used to make requests.

    This test ensures that the server returns a 429 Too Many Requests status code
    and the appropriate error message when the rate limit for account activation
    requests is exceeded.
    """
    expected_status_code = status.HTTP_429_TOO_MANY_REQUESTS
    expected_message = "Request was throttled."
    expected_error_code = "throttled"

    # Simulate multiple POST requests to exceed the rate limit
    client.post(url)
    client.post(url)
    client.post(url)
    client.post(url)
    client.post(url)
    response = client.post(url)

    assert expected_status_code == response.status_code
    assert expected_message in response.data["message"]
    assert expected_error_code == response.data["error_code"]
