from datetime import timedelta
from unittest.mock import MagicMock, patch

import jwt
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from user_app.constants import http_response
from user_app.models import ChangeEmailCodeModel
from user_app.tests.constants import (
    ALLOW_REQUEST_FUNCTION_TO_PATCH,
    EMAIL_CHANGE_VIEWS_MODULE_PATH,
    FAKE_SECRET,
    TOKEN_SECRET_SETTING_TO_PATCH,
    TOKEN_SERVICE_MODULE_PATH,
    Account,
)

# =========== Objects and constants ==============
url: str = reverse("change_email")
NON_EXISTENT_CODE = "non_existent_code"
OLD_EMAIL = "actual_email@email.com"
NEW_EMAIL = "new_email@email.com"


# ============ Fixtures ================
@pytest.fixture
def account():
    """Creates and returns a Account object for use in tests."""
    return Account.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email=OLD_EMAIL,
        password="1234@!AA",
        is_active=True,
    )


@pytest.fixture
def client(account) -> APIClient:
    """
    Provides an API client with JWT authentication in the request header.

    Returns:
        APIClient: An API client with the Authorization header set to a valid JWT token.
    """
    token = jwt.encode(
        {
            "uid": account.id,
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
def code(account) -> str:
    """
    Creates and returns a valid verification code
    for changing the account's email.
    """
    return ChangeEmailCodeModel.objects.create(
        account=account, new_email=NEW_EMAIL
    ).code


@pytest.fixture
def expired_code(account) -> str:
    """
    Creates and returns an expired verification code for
    testing expiration scenarios.
    """
    return ChangeEmailCodeModel.objects.create(
        account=account,
        new_email=NEW_EMAIL,
        expires_at=timezone.now() - timedelta(minutes=1),
    ).code


# ============ Tests ================
@pytest.mark.django_db
@patch(
    f"{EMAIL_CHANGE_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_do_not_change_email_if_code_does_not_exist(
    allow_request_function_mock: MagicMock, client: APIClient
):
    """
    This test verifies that when a non-existent change email code is provided,
    the system returns an appropriate error response.

    Mocked elements:
    - allow_request_function_mock: Mocks the rate limit allowing the request
                                   to proceed.
    """
    expected_detail_message = http_response.CODE_NOT_FOUND["detail"]
    expected_code = http_response.CODE_NOT_FOUND["code"]
    expected_status_code = status.HTTP_404_NOT_FOUND

    actual_response = client.post(url, data={"code": NON_EXISTENT_CODE}, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
@patch(
    f"{EMAIL_CHANGE_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_do_not_change_email_if_code_is_expired(
    allow_request_function_mock: MagicMock, client: APIClient, expired_code: str
):
    """
    This test ensures that when an expired email change code is provided,
    the system returns the correct error response indicating the code has expired.

    Mocked elements:
    - allow_request_function_mock: Mocks the rate limit, allowing the request
                                   to proceed.
    """
    expected_detail_message = http_response.CODE_EXPIRED["detail"]
    expected_code = http_response.CODE_EXPIRED["code"]
    expected_status_code = status.HTTP_410_GONE

    actual_response = client.post(url, data={"code": expired_code}, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
@patch(
    f"{EMAIL_CHANGE_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_delete_code_if_expired(
    allow_request_function_mock: MagicMock, client: APIClient, expired_code: str
):
    """
    When it is verified that the code has expired, it must be
    removed from the database.

    Mocked elements:
    - allow_request_function_mock: Mocks the rate limit, allowing the request
                                   to proceed.
    """
    client.post(url, data={"code": expired_code}, format="json")
    assert not ChangeEmailCodeModel.objects.filter(code=expired_code).exists()


@pytest.mark.django_db
@patch(
    f"{EMAIL_CHANGE_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_change_email_successful(
    allow_request_function_mock: MagicMock, client: APIClient, code: str
):
    """
    This test ensures that an account's email is successfully updated when a valid
    email change code is provided.

    Mocked elements:
    - allow_request_function_mock: Mocks the rate limit, allowing the request
                                   to proceed.
    """
    expected_detail_message = http_response.ACCOUNT_EMAIL_CHANGED["detail"]
    expected_code = http_response.ACCOUNT_EMAIL_CHANGED["code"]
    expected_status_code = status.HTTP_200_OK

    # Checks if there's account with old email in database, before change.
    assert Account.objects.filter(email=OLD_EMAIL).exists()

    actual_response = client.post(url, data={"code": code}, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    # Check if pair token is included in response.
    assert "access" and "refresh" in actual_response.data
    # Checks if account with new email exists.
    assert Account.objects.filter(email=NEW_EMAIL).exists()
    # Checks if account with old email not exists.
    assert not Account.objects.filter(email=OLD_EMAIL).exists()


@pytest.mark.django_db
@patch(
    f"{EMAIL_CHANGE_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_delete_code_when_account_email_changed_successfully(
    allow_request_function_mock: MagicMock, client: APIClient, code: str
):
    """
    After the account's email has been changed, the code must be
    removed from the database.

    Mocked elements:
    - allow_request_function_mock: Mocks the rate limit, allowing the request
                                   to proceed.
    """
    # Checks if there's code in database before change.
    assert ChangeEmailCodeModel.objects.filter(code=code).exists()
    client.post(url, data={"code": code}, format="json")
    assert not ChangeEmailCodeModel.objects.filter(code=code).exists()


@pytest.mark.django_db
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_does_not_change_email_when_request_limit_is_reached(client: APIClient):
    """
    This test ensures that the API enforces rate limiting and returns an error when
    the number of allowed requests is exceeded.
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
