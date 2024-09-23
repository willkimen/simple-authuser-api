from datetime import timedelta
from unittest.mock import MagicMock, patch

import jwt
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from user_app.constants import response_code_messages
from user_app.constants.path_for_mock import (
    change_email_view_path,
    token_utils_module_path,
)
from user_app.models import ChangeEmailCodeModel

# =========== Objects and constants ==============
User = get_user_model()
url: str = reverse("change_user_email")
allow_request = "FivePerMinuteRateLimit.allow_request"
send_change_email_code_by_email = "send_change_email_code_by_email"
os_environ_get = "os.environ.get"
SECRET = "token_secret"
NON_EXISTENT_CODE = "non_existent_code"
OLD_EMAIL = "actual_email@email.com"
NEW_EMAIL = "new_email@email.com"


# ============ Fixtures ================
@pytest.fixture
def user() -> User:
    """Creates and returns a User object for use in tests."""
    return User.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email=OLD_EMAIL,
        password="1234@!AA",
        is_active=True,
    )


@pytest.fixture
def client(user: User) -> APIClient:
    """
    Provides an API client with JWT authentication in the request header.

    Returns:
        APIClient: An API client with the Authorization header set to a valid JWT token.
    """
    token = jwt.encode(
        {
            "uid": user.id,
            "typ": "access",
            "jti": "fake_jti",
            "exp": int((timezone.now() + timedelta(seconds=60)).timestamp()),
        },
        SECRET,
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def code(user: User) -> str:
    """Creates and returns a valid confirmation code for changing the user's email."""
    return ChangeEmailCodeModel.objects.create(
        user=user,
        new_email=NEW_EMAIL,
    ).code


@pytest.fixture
def expired_code(user: User) -> str:
    """Creates and returns an expired confirmation code for testing expiration scenarios."""
    return ChangeEmailCodeModel.objects.create(
        user=user,
        new_email=NEW_EMAIL,
        expires_at=timezone.now() - timedelta(minutes=1),
    ).code


# ============ Tests ================
@pytest.mark.django_db
@patch(
    f"{change_email_view_path}.{allow_request}",
    return_value=True,
)
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
def test_do_not_change_email_if_code_does_not_exist(
    token_secret_mock: MagicMock,
    mock_allow_request: MagicMock,
    client: APIClient,
):
    expected_detail_message = response_code_messages.CODE_NOT_FOUND["detail"]
    expected_code = response_code_messages.CODE_NOT_FOUND["code"]
    expected_status_code = status.HTTP_404_NOT_FOUND

    actual_response = client.post(url, data={"code": NON_EXISTENT_CODE}, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
@patch(
    f"{change_email_view_path}.{allow_request}",
    return_value=True,
)
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
def test_do_not_change_email_if_code_is_expired(
    token_secret_mock: MagicMock,
    mock_allow_request: MagicMock,
    client: APIClient,
    expired_code: str,
):
    expected_detail_message = response_code_messages.CODE_EXPIRED["detail"]
    expected_code = response_code_messages.CODE_EXPIRED["code"]
    expected_status_code = status.HTTP_410_GONE

    actual_response = client.post(url, data={"code": expired_code}, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
@patch(
    f"{change_email_view_path}.{allow_request}",
    return_value=True,
)
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
def test_delete_code_if_expired(
    token_secret_mock: MagicMock,
    mock_allow_request: MagicMock,
    client: APIClient,
    expired_code: str,
):
    """
    When it is verified that the code has expired, it must be
    removed from the database.
    """
    client.post(url, data={"code": expired_code}, format="json")
    assert not ChangeEmailCodeModel.objects.filter(code=expired_code).exists()


@pytest.mark.django_db
@patch(
    f"{change_email_view_path}.{allow_request}",
    return_value=True,
)
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
def test_change_email_successful(
    token_secret_mock: MagicMock,
    mock_allow_request: MagicMock,
    client: APIClient,
    code: str,
):
    expected_detail_message = response_code_messages.USER_EMAIL_CHANGED["detail"]
    expected_code = response_code_messages.USER_EMAIL_CHANGED["code"]
    expected_status_code = status.HTTP_200_OK

    # Checks if there's user with old email in database, before change.
    assert User.objects.filter(email=OLD_EMAIL).exists()

    actual_response = client.post(url, data={"code": code}, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    # Checks if user with new email exists.
    assert User.objects.filter(email=NEW_EMAIL).exists()
    # Checks if user with old email not exists.
    assert not User.objects.filter(email=OLD_EMAIL).exists()


@pytest.mark.django_db
@patch(
    f"{change_email_view_path}.{allow_request}",
    return_value=True,
)
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
def test_delete_code_when_user_email_changed_successfully(
    token_secret_mock: MagicMock,
    mock_allow_request: MagicMock,
    client: APIClient,
    code: str,
):
    """
    After the user's email has been changed, the code must be
    removed from the database.
    """
    # Checks if there's code in database before change.
    assert ChangeEmailCodeModel.objects.filter(code=code).exists()
    client.post(url, data={"code": code}, format="json")
    assert not ChangeEmailCodeModel.objects.filter(code=code).exists()


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
def test_does_not_change_email_when_request_limit_is_reached(
    token_secret_mock: MagicMock, client: APIClient
):
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
