"""
This module contains tests for the JWT refresh functionality.
It verifies the behavior of the JWT refresh endpoint (`refresh_token_access`). 
The endpoint expects a refresh token and returns a new access token if 
the provided refresh token is valid. It handles various scenarios including 
blacklisted tokens, non-existent users, and inactive users.
"""

from datetime import timedelta
from unittest.mock import patch

import jwt
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from user_app.constants import response_codes_and_messages, token_exception_messages
from user_app.constants.path_for_mock import token_utils_module_path
from user_app.models import BlacklistTokenModel

# =========== Objects and constants ==============
User = get_user_model()
url: str = reverse("refresh_token_access")
SECRET = "token_secret"
UID_NON_EXIST = 100
UID = 1
INCORRECT_TYP = "access"
token_secret_mock = "settings.TOKEN_SECRET"


# ============ Fixtures ================
@pytest.fixture
def client() -> APIClient:
    """
    Provides an API client for making HTTP requests.

    Returns:
        APIClient: An instance of the Django REST Framework APIClient.
    """
    return APIClient()


@pytest.fixture
def activated_user():
    return User.objects.create(
        id=UID,
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fakeemail@email.com",
        is_active=True,
    )


@pytest.fixture
def payload(activated_user) -> dict:
    return {
        "uid": activated_user.id,
        "typ": "refresh",
        "jti": "fake_jti",
        "exp": int((timezone.now() + timedelta(seconds=60)).timestamp()),
    }


@pytest.fixture
def blacklisted_refresh_token(payload: dict) -> str:
    """
    Provides a refresh token that is blacklisted.

    Returns:
        str: An encoded JWT refresh token that is in the blacklist.
    """

    BlacklistTokenModel.objects.create(
        user_id=payload["uid"],
        jti=payload["jti"],
        typ=payload["typ"],
        exp=payload["exp"],
    )

    return jwt.encode(payload, SECRET)


@pytest.fixture
def incorrect_type_token(payload: dict) -> str:
    """
    Provides a valid access token with an incorrect token type.

    This fixture creates a token with a type that is not expected by
    the refresh token endpoint.
    The token has a valid structure but uses an incorrect 'typ' field.

    Returns:
        str: An encoded JWT token with an incorrect type.
    """
    payload["typ"] = INCORRECT_TYP
    return jwt.encode(payload, SECRET)


@pytest.fixture
def refresh_token_for_nonexistent_user(payload: dict) -> str:
    """
    Provides a refresh token for a non-existent user.

    Returns:
        str: An encoded JWT refresh token for a non-existent user.
    """
    payload["uid"] = UID_NON_EXIST
    return jwt.encode(payload, SECRET)


@pytest.fixture
def refresh_token_for_inactive_user(payload: dict) -> str:
    """
    Provides a refresh token for an inactive user.

    Returns:
        str: An encoded JWT refresh token for an inactive user.
    """
    inactive_user = User.objects.create(
        id=20,
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fakeotheremail@email.com",
        is_active=False,
    )
    payload["uid"] = inactive_user.id

    return jwt.encode(payload, SECRET)


@pytest.fixture
def valid_refresh_token(payload: dict) -> str:
    """
    Provides a valid refresh token.

    This fixture creates a user and generates a valid refresh token.

    Returns:
        str: An encoded JWT refresh token for an active user.
    """
    return jwt.encode(payload, SECRET)


# ========== Tests ================
@pytest.mark.django_db
@patch(f"{token_utils_module_path}.{token_secret_mock}", SECRET)
def test_blacklisted_refresh_token_not_generate_new_access_token(
    client: APIClient, blacklisted_refresh_token: str
):
    """
    Tests that a blacklisted refresh token does not generate a new access token.

    Args:
        mock_secret (MagicMock): Mocked JWT secret environment variable.
        client (APIClient): The test client used to make HTTP requests.
        blacklisted_refresh_token (str): The refresh token that is blacklisted.
    """
    expected_detail_message = token_exception_messages.TOKEN_IN_BLACKLIST["detail"]
    expected_code = token_exception_messages.TOKEN_IN_BLACKLIST["code"]
    expected_status_code = status.HTTP_403_FORBIDDEN

    actual_response = client.post(
        url, data={"refresh": blacklisted_refresh_token}, format="json"
    )

    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert expected_status_code == actual_response.status_code


@pytest.mark.django_db
@patch(f"{token_utils_module_path}.{token_secret_mock}", SECRET)
def test_non_refresh_token_not_generate_new_access_token(
    client: APIClient, incorrect_type_token: str
):
    """
    Tests that a non-refresh token does not generate a new access token.

    Args:
        mock_secret (MagicMock): Mocked JWT secret environment variable.
        client (APIClient): The test client used to make HTTP requests.
        incorrect_type_token (str): The JWT access token provided as a refresh token.
    """
    expected_detail_message = response_codes_and_messages.IS_NOT_REFRESH_TOKEN["detail"]
    expected_code = response_codes_and_messages.IS_NOT_REFRESH_TOKEN["code"]
    expected_status_code = status.HTTP_400_BAD_REQUEST

    actual_response = client.post(
        url, data={"refresh": incorrect_type_token}, format="json"
    )

    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert expected_status_code == actual_response.status_code


@pytest.mark.django_db
@patch(f"{token_utils_module_path}.{token_secret_mock}", SECRET)
def test_nonexistent_user_not_generate_access_token(
    client: APIClient, refresh_token_for_nonexistent_user: str
):
    """
    Tests that a refresh token for a non-existent user does not
    generate an access token.

    Args:
        mock_secret (MagicMock): Mocked JWT secret environment variable.
        client (APIClient): The test client used to make HTTP requests.
        refresh_token_for_nonexistent_user (str): The refresh token for a
                                                  non-existent user.
    """
    expected_detail_message = response_codes_and_messages.USER_NOT_FOUND["detail"]
    expected_code = response_codes_and_messages.USER_NOT_FOUND["code"]
    expected_status_code = status.HTTP_404_NOT_FOUND

    actual_response = client.post(
        url, data={"refresh": refresh_token_for_nonexistent_user}, format="json"
    )

    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert expected_status_code == actual_response.status_code


@pytest.mark.django_db
@patch(f"{token_utils_module_path}.{token_secret_mock}", SECRET)
def test_inactive_user_not_generate_access_token(
    client: APIClient, refresh_token_for_inactive_user: str
):
    """
    Tests that a refresh token for an inactive user does not generate an access token.

    Args:
        mock_secret (MagicMock): Mocked JWT secret environment variable.
        client (APIClient): The test client used to make HTTP requests.
        refresh_token_for_inactive_user (str): The refresh token for an inactive user.
    """
    expected_detail_message = response_codes_and_messages.USER_ACCOUNT_NOT_ACTIVATED[
        "detail"
    ]
    expected_code = response_codes_and_messages.USER_ACCOUNT_NOT_ACTIVATED["code"]
    expected_status_code = status.HTTP_403_FORBIDDEN

    actual_response = client.post(
        url, data={"refresh": refresh_token_for_inactive_user}, format="json"
    )

    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert expected_status_code == actual_response.status_code


@pytest.mark.django_db
@patch(f"{token_utils_module_path}.{token_secret_mock}", SECRET)
def test_valid_refresh_token_creates_access_token(
    client: APIClient, valid_refresh_token: str
):
    """
    Tests that a valid refresh token successfully generates a new access token.

    Args:
        mock_secret (MagicMock): Mocked JWT secret environment variable.
        client (APIClient): The test client used to make HTTP requests.
        valid_refresh_token (str): The valid refresh token.
    """
    expected_detail_message = response_codes_and_messages.TOKEN_ACCESS_CREATED["detail"]
    expected_code = response_codes_and_messages.TOKEN_ACCESS_CREATED["code"]
    expected_status_code = status.HTTP_201_CREATED
    expected_typ_payload = "access"
    expected_uid_payload = UID

    actual_response = client.post(
        url, data={"refresh": valid_refresh_token}, format="json"
    )

    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert expected_status_code == actual_response.status_code

    actual_payload = jwt.decode(
        actual_response.data["access"], SECRET, algorithms="HS256"
    )
    assert expected_typ_payload == actual_payload["typ"]
    assert expected_uid_payload == actual_payload["uid"]
