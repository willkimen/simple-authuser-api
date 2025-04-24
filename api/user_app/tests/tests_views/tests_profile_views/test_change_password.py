from datetime import timedelta
from unittest.mock import MagicMock, patch

import jwt
import pytest
from django.contrib.auth.hashers import check_password
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from user_app.constants import response_codes_and_messages
from user_app.tests.constants import (
    FAKE_SECRET,
    PROFILE_VIEWS_MODULE_PATH,
    REVOKE_TOKENS_FUNCTION_TO_PATCH,
    TOKEN_SECRET_SETTING_TO_PATCH,
    TOKEN_UTILS_MODULE_PATH,
    User,
)

# =========== Objects and constants ==============
url: str = reverse("change_password")
ACTUAL_PASSWORD = "FAKE_actual_password10!"
NEW_PASSWORD = "FAKE_new_password10!"
DIFFERENT_ACTUAL_PASSWORD = "FAKE_different_password10!"
USER_ID = 1


# ============ Fixtures ================
@pytest.fixture
def user():
    """Creates and returns a User object for use in tests."""
    return User.objects.create_user(
        id=USER_ID,
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fakeemail@email.com",
        password=ACTUAL_PASSWORD,
        is_active=True,
    )


@pytest.fixture
def client(user) -> APIClient:
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
        FAKE_SECRET,
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


# ============ Tests ================
@pytest.mark.django_db
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
@patch(f"{PROFILE_VIEWS_MODULE_PATH}.{REVOKE_TOKENS_FUNCTION_TO_PATCH}")
def test_password_not_changed_when_actual_password_does_not_match(
    revoke_tokens_function_mock: MagicMock, client: APIClient
):
    """
    Test that the password is not changed when the current password does not match.
    """
    expected_detail_message = response_codes_and_messages.PASSWORD_INCORRECT["detail"]
    expected_code = response_codes_and_messages.PASSWORD_INCORRECT["code"]
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
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
@patch(f"{PROFILE_VIEWS_MODULE_PATH}.{REVOKE_TOKENS_FUNCTION_TO_PATCH}")
def test_change_password_successfully(
    revoke_tokens_function_mock: MagicMock, client: APIClient
):
    """
    Test that the password is changed successfully.
    """
    expected_detail_message = response_codes_and_messages.USER_PASSWORD_CHANGED[
        "detail"
    ]
    expected_code = response_codes_and_messages.USER_PASSWORD_CHANGED["code"]
    expected_status_code = status.HTTP_200_OK

    actual_response = client.patch(
        url,
        data={"actual_password": ACTUAL_PASSWORD, "new_password": NEW_PASSWORD},
        format="json",
    )

    # Get the user after the request, to get the password change.
    user = User.objects.get(id=USER_ID)

    assert check_password(ACTUAL_PASSWORD, user.password) == False
    assert check_password(NEW_PASSWORD, user.password) == True
    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
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
