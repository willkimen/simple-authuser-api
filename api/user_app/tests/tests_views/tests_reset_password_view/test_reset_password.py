from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from user_app.constants import response_codes_and_messages
from user_app.constants.path_for_mock import (
    reset_password_view,
    token_utils_module_path,
)
from user_app.models import ResetPasswordCodeModel

# =========== Objects and constants ==============
User = get_user_model()
url: str = reverse("reset_password")
allow_request = "FivePerMinuteRateLimit.allow_request"
revoke_tokens_mock = "revoke_tokens"
token_secret_mock_mock = "settings.TOKEN_SECRET"
SECRET = "token_secret"
NON_EXISTENT_CODE = "NON_EXISTENT_CODE"
OLD_PASSWORD = "FAKEOLDpassword!10"
NEW_PASSWORD = "FAKEpassword!10"
CONFIRMATION_NEW_PASSWORD = "FAKEpassword!10"
USER_ID = 100


# ============ Fixtures ================
@pytest.fixture
def client() -> APIClient:
    """
    This client is used to send HTTP requests in the tests.
    """
    return APIClient()


@pytest.fixture
def activated_user():
    """
    Fixture to create and return an activated User object.
    """
    return User.objects.create_user(
        id=USER_ID,
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fakeemail@email.com",
        password=OLD_PASSWORD,
        is_active=True,
    )


@pytest.fixture
def expired_code(activated_user) -> str:
    return ResetPasswordCodeModel.objects.create(
        user=activated_user, expires_at=timezone.now() - timedelta(minutes=1)
    ).code


@pytest.fixture
def valid_code(activated_user) -> str:
    return ResetPasswordCodeModel.objects.create(user=activated_user).code


# ============ Tests ================
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
@patch(f"{reset_password_view}.{allow_request}", return_value=True)
def test_does_not_reset_when_non_existent_code(
    mock_allow_request: MagicMock, client: APIClient
):
    """
    Tests if the system returns an error when attempting to
    reset the password with a non-existent code.
    """
    expected_detail_message = response_codes_and_messages.CODE_NOT_FOUND["detail"]
    expected_code = response_codes_and_messages.CODE_NOT_FOUND["code"]
    expected_status_code = status.HTTP_404_NOT_FOUND

    actual_response = client.post(
        url,
        data={
            "code": NON_EXISTENT_CODE,
            "new_password": NEW_PASSWORD,
            "confirmation_new_password": CONFIRMATION_NEW_PASSWORD,
        },
        format="json",
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
@patch(f"{reset_password_view}.{allow_request}", return_value=True)
def test_does_not_reset_when_expired_code(
    mock_allow_request: MagicMock, client: APIClient, expired_code: str
):
    """
    Tests if the system returns an error when attempting to reset the password with
    an expired code.
    """
    expected_detail_message = response_codes_and_messages.CODE_EXPIRED["detail"]
    expected_code = response_codes_and_messages.CODE_EXPIRED["code"]
    expected_status_code = status.HTTP_410_GONE

    actual_response = client.post(
        url,
        data={
            "code": expired_code,
            "new_password": NEW_PASSWORD,
            "confirmation_new_password": CONFIRMATION_NEW_PASSWORD,
        },
        format="json",
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
@patch(f"{reset_password_view}.{allow_request}", return_value=True)
def test_expired_code_is_deleted(
    mock_allow_request: MagicMock, client: APIClient, expired_code: str
):
    """
    Tests if the expired code is deleted after being used.
    """
    assert ResetPasswordCodeModel.objects.filter(code=expired_code).exists()

    client.post(
        url,
        data={
            "code": expired_code,
            "new_password": NEW_PASSWORD,
            "confirmation_new_password": CONFIRMATION_NEW_PASSWORD,
        },
        format="json",
    )

    assert not ResetPasswordCodeModel.objects.filter(code=expired_code).exists()


@pytest.mark.django_db
@patch(f"{reset_password_view}.{allow_request}", return_value=True)
@patch(f"{reset_password_view}.{revoke_tokens_mock}")
def test_after_reset_password_the_code_is_deleted(
    revoke_tokens_mock: MagicMock,
    mock_allow_request: MagicMock,
    client: APIClient,
    valid_code: str,
):
    """
    Tests if the password reset code is deleted after a successful password reset and
    if the user's tokens are revoked.
    """
    assert ResetPasswordCodeModel.objects.filter(code=valid_code).exists()

    client.post(
        url,
        data={
            "code": valid_code,
            "new_password": NEW_PASSWORD,
            "confirmation_new_password": CONFIRMATION_NEW_PASSWORD,
        },
        format="json",
    )

    assert not ResetPasswordCodeModel.objects.filter(code=valid_code).exists()

    revoke_tokens_mock.assert_called()


@pytest.mark.django_db
@patch(f"{reset_password_view}.{allow_request}", return_value=True)
@patch(f"{token_utils_module_path}.{token_secret_mock_mock}", SECRET)
def test_reset_password_successful(
    mock_allow_request: MagicMock, client: APIClient, valid_code: str
):
    """
    Tests if the password reset process is successful with a valid code and
    if new tokens are generated correctly.
    """
    expected_detail_message = response_codes_and_messages.USER_PASSWORD_RESET["detail"]
    expected_code = response_codes_and_messages.USER_PASSWORD_RESET["code"]
    expected_status_code = status.HTTP_200_OK

    actual_response = client.post(
        url,
        data={
            "code": valid_code,
            "new_password": NEW_PASSWORD,
            "confirmation_new_password": CONFIRMATION_NEW_PASSWORD,
        },
        format="json",
    )

    user = User.objects.get(id=USER_ID)
    assert check_password(NEW_PASSWORD, user.password)
    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert "access" and "refresh" in actual_response.data
