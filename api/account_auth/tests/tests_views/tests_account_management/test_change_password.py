from datetime import timedelta
from unittest.mock import MagicMock, patch

import jwt
import pytest
from django.contrib.auth.hashers import check_password
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from account_auth.constants import http_response
from account_auth.tests.constants import (
    FAKE_SECRET,
    ACCOUNT_MANAGEMENT_VIEWS_MODULE_PATH,
    REVOKE_TOKENS_FUNCTION_TO_PATCH,
    TOKEN_SECRET_SETTING_TO_PATCH,
    TOKEN_SERVICE_MODULE_PATH,
    Account,
)

# =========== Objects and constants ==============
url: str = reverse("change_password")
ACTUAL_PASSWORD = "FAKE_actual_password10!"
NEW_PASSWORD = "FAKE_new_password10!"
DIFFERENT_ACTUAL_PASSWORD = "FAKE_different_password10!"
ACCOUNT_ID = 1


# ============ Fixtures ================
@pytest.fixture
def account():
    """Creates and returns a Account object for use in tests."""
    return Account.objects.create_user(
        id=ACCOUNT_ID,
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fakeemail@email.com",
        password=ACTUAL_PASSWORD,
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


# ============ Tests ================
@pytest.mark.django_db
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
@patch(f"{ACCOUNT_MANAGEMENT_VIEWS_MODULE_PATH}.{REVOKE_TOKENS_FUNCTION_TO_PATCH}")
def test_password_not_changed_when_actual_password_does_not_match(
    revoke_tokens_function_mock: MagicMock, client: APIClient
):
    """
    Test that the password is not changed when the current password does not match.
    """
    expected_detail_message = http_response.PASSWORD_INCORRECT["detail"]
    expected_code = http_response.PASSWORD_INCORRECT["code"]
    expected_status_code = status.HTTP_400_BAD_REQUEST

    actual_response = client.patch(
        url,
        data={
            "actual_password": DIFFERENT_ACTUAL_PASSWORD,
            "new_password": NEW_PASSWORD,
        },
        format="json",
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
@patch(f"{ACCOUNT_MANAGEMENT_VIEWS_MODULE_PATH}.{REVOKE_TOKENS_FUNCTION_TO_PATCH}")
def test_change_password_successfully(
    revoke_tokens_function_mock: MagicMock, client: APIClient
):
    """
    Test that the password is changed successfully.
    """
    expected_detail_message = http_response.ACCOUNT_PASSWORD_CHANGED["detail"]
    expected_code = http_response.ACCOUNT_PASSWORD_CHANGED["code"]
    expected_status_code = status.HTTP_200_OK

    actual_response = client.patch(
        url,
        data={"actual_password": ACTUAL_PASSWORD, "new_password": NEW_PASSWORD},
        format="json",
    )

    # Get the account after the request, to get the password change.
    account = Account.objects.get(id=ACCOUNT_ID)

    assert check_password(ACTUAL_PASSWORD, account.password) == False
    assert check_password(NEW_PASSWORD, account.password) == True
    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_new_tokens_returned_when_password_is_changed_successfully(client: APIClient):
    """
    Test that new tokens are returned when the password is changed successfully.
    """
    actual_response = client.patch(
        url,
        data={"actual_password": ACTUAL_PASSWORD, "new_password": NEW_PASSWORD},
        format="json",
    )

    assert "access" and "refresh" in actual_response.data
