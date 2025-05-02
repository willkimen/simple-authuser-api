from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.hashers import check_password
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from user_app.constants import http_response
from user_app.models import ResetPasswordCodeModel
from user_app.tests.constants import (
    ALLOW_REQUEST_FUNCTION_TO_PATCH,
    FAKE_SECRET,
    RESET_PASSWORD_VIEWS_MODULE_PATH,
    REVOKE_TOKENS_FUNCTION_TO_PATCH,
    TOKEN_SECRET_SETTING_TO_PATCH,
    TOKEN_UTILS_MODULE_PATH,
    Account,
)

# =========== Objects and constants ==============
url: str = reverse("reset_password")
NON_EXISTENT_CODE = "NON_EXISTENT_CODE"
OLD_PASSWORD = "FAKEOLDpassword!10"
NEW_PASSWORD = "FAKEpassword!10"
CONFIRMATION_NEW_PASSWORD = "FAKEpassword!10"
ACCOUNT_ID = 100


# ============ Fixtures ================
@pytest.fixture
def activated_account():
    """
    Fixture to create and return an activated Account object.
    """
    return Account.objects.create_user(
        id=ACCOUNT_ID,
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fakeemail@email.com",
        password=OLD_PASSWORD,
        is_active=True,
    )


@pytest.fixture
def expired_code(activated_account) -> str:
    return ResetPasswordCodeModel.objects.create(
        account=activated_account, expires_at=timezone.now() - timedelta(minutes=1)
    ).code


@pytest.fixture
def valid_code(activated_account) -> str:
    return ResetPasswordCodeModel.objects.create(account=activated_account).code


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
@patch(
    f"{RESET_PASSWORD_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_does_not_reset_when_non_existent_code(
    allow_request_function_mock: MagicMock, client: APIClient
):
    """
    Tests if the system returns an error when attempting to
    reset the password with a non-existent code.
    """
    expected_detail_message = http_response.CODE_NOT_FOUND["detail"]
    expected_code = http_response.CODE_NOT_FOUND["code"]
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
@patch(
    f"{RESET_PASSWORD_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_does_not_reset_when_expired_code(
    allow_request_function_mock: MagicMock, client: APIClient, expired_code: str
):
    """
    Tests if the system returns an error when attempting to reset the password with
    an expired code.
    """
    expected_detail_message = http_response.CODE_EXPIRED["detail"]
    expected_code = http_response.CODE_EXPIRED["code"]
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
@patch(
    f"{RESET_PASSWORD_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_expired_code_is_deleted(
    allow_request_function_mock: MagicMock, client: APIClient, expired_code: str
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
@patch(
    f"{RESET_PASSWORD_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
@patch(f"{RESET_PASSWORD_VIEWS_MODULE_PATH}.{REVOKE_TOKENS_FUNCTION_TO_PATCH}")
def test_after_reset_password_the_code_is_deleted(
    revoke_tokens_function_mock: MagicMock,
    allow_request_function_mock: MagicMock,
    client: APIClient,
    valid_code: str,
):
    """
    Tests if the password reset code is deleted after a successful password reset and
    if the account's tokens are revoked.
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

    revoke_tokens_function_mock.assert_called()


@pytest.mark.django_db
@patch(
    f"{RESET_PASSWORD_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_reset_password_successful(
    allow_request_function_mock: MagicMock, client: APIClient, valid_code: str
):
    """
    Tests if the password reset process is successful with a valid code and
    if new tokens are generated correctly.
    """
    expected_detail_message = http_response.ACCOUNT_PASSWORD_RESET["detail"]
    expected_code = http_response.ACCOUNT_PASSWORD_RESET["code"]
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

    account = Account.objects.get(id=ACCOUNT_ID)
    assert check_password(NEW_PASSWORD, account.password)
    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert "access" and "refresh" in actual_response.data
