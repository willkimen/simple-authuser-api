"""
Tests blacklist_token() view.  
"""

from datetime import timedelta
from unittest.mock import MagicMock, patch

import jwt
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from user_app.constants import response_code_messages, token_exception_messages
from user_app.constants.path_for_mock import token_utils_module_path
from user_app.models import BlacklistTokenModel

# =========== Objects and constants ==============
User = get_user_model()
url: str = reverse("blacklist_token")
FAKE_SECRET = "token_secret"
FAKE_TYP = "access"
FAKE_JTI = "fake_jti"
FAKE_UID = 1
INCORRECT_TYP = "incorrect_type"
FAKE_EXP = int((timezone.now() + timedelta(seconds=60)).timestamp())
FAKE_USER_DATA = {
    "id": FAKE_UID,
    "first_name": "fake_first_name",
    "last_name": "fake_last_name",
    "email": "fake@email.com",
    "password": "FAKEpassword10!",
}
os_environ_get_path_for_mock = "os.environ.get"


# ============ Fixtures ================
@pytest.fixture
def client_auth_header() -> APIClient:
    """
    Provides an API client with JWT authentication in the request header.

    Returns:
        APIClient: An API client with the Authorization header set to a valid JWT token.
    """
    user = User.objects.create_user(**FAKE_USER_DATA, is_active=True)
    token = jwt.encode(
        {
            "uid": user.id,
            "typ": FAKE_TYP,
            "jti": "fake_jti_for_auth_header",
            "exp": FAKE_EXP,
        },
        FAKE_SECRET,
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def blacklisted_token() -> str:
    """
    Creates and provides a blacklisted JWT token for testing.

    Returns:
        str: A JWT token that is blacklisted.
    """
    payload = {
        "uid": FAKE_UID,
        "typ": FAKE_TYP,
        "jti": FAKE_JTI,
        "exp": FAKE_EXP,
    }
    BlacklistTokenModel.objects.create(
        user_id=FAKE_UID,
        jti=payload["jti"],
        typ=payload["typ"],
        exp=payload["exp"],
    )

    return jwt.encode(payload, FAKE_SECRET)


@pytest.fixture
def incorrect_typ_token() -> str:
    """
    Provides a JWT token with an incorrect type for testing.

    Returns:
        str: A JWT token with an incorrect type field ("typ").
    """
    payload = {
        "uid": FAKE_UID,
        "typ": INCORRECT_TYP,
        "jti": FAKE_JTI,
        "exp": FAKE_EXP,
    }

    return jwt.encode(payload, FAKE_SECRET)


@pytest.fixture
def token_with_different_user_id() -> str:
    """
    Provides a JWT token for a different user, to test token-user mismatches.

    Returns:
        str: A JWT token with a user ID different from the one making the request.
    """
    USER_DATA = {
        "id": 100,
        "first_name": "fake_first_name",
        "last_name": "fake_last_name",
        "email": "fake2@email.com",
        "password": "FAKEpassword10!",
    }
    user = User.objects.create_user(**USER_DATA, is_active=True)
    payload = {
        "uid": user.id,
        "typ": FAKE_TYP,
        "jti": FAKE_JTI,
        "exp": FAKE_EXP,
    }

    return jwt.encode(payload, FAKE_SECRET)


@pytest.fixture
def valid_token() -> str:
    """
    Provides a valid JWT token for testing.

    Returns:
        str: A valid JWT token for an active user.
    """
    user = User.objects.create_user(**FAKE_USER_DATA, is_active=True)
    payload = {
        "uid": user.id,
        "typ": FAKE_TYP,
        "jti": FAKE_JTI,
        "exp": FAKE_EXP,
    }

    return jwt.encode(payload, FAKE_SECRET)


# ========== Tests ================
@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get_path_for_mock}",
    return_value=FAKE_SECRET,
)
def test_token_already_in_blacklist(
    mock_secret: MagicMock, client_auth_header: APIClient, blacklisted_token: str
):
    """
    Test that a JWT token already blacklisted returns the appropriate error message.
    """
    expected_detail_message = token_exception_messages.TOKEN_IN_BLACKLIST["detail"]
    expected_code = token_exception_messages.TOKEN_IN_BLACKLIST["code"]
    expected_status_code = status.HTTP_403_FORBIDDEN

    actual_response = client_auth_header.post(
        url, data={"token": blacklisted_token}, format="json"
    )
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert expected_status_code == actual_response.status_code


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get_path_for_mock}",
    return_value=FAKE_SECRET,
)
def test_token_type_must_be_access_or_refresh(
    mock_secret: MagicMock, client_auth_header: APIClient, incorrect_typ_token: str
):
    """
    Test that a JWT token with an incorrect type field ("typ") returns the appropriate error.
    """
    expected_detail_message = response_code_messages.IS_NOT_ACCESS_OR_REFRESH_TOKEN[
        "detail"
    ]
    expected_code = response_code_messages.IS_NOT_ACCESS_OR_REFRESH_TOKEN["code"]
    expected_status_code = status.HTTP_400_BAD_REQUEST

    actual_response = client_auth_header.post(
        url, data={"token": incorrect_typ_token}, format="json"
    )
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert expected_status_code == actual_response.status_code


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get_path_for_mock}",
    return_value=FAKE_SECRET,
)
def test_user_must_match_token_owner(
    mock_secret: MagicMock,
    client_auth_header: APIClient,
    token_with_different_user_id: str,
):
    """
    Test that a token's user ID must match the authenticated user's ID for the request to succeed.
    """
    expected_detail_message = response_code_messages.USER_TOKEN_MISMATCH["detail"]
    expected_code = response_code_messages.USER_TOKEN_MISMATCH["code"]
    expected_status_code = status.HTTP_403_FORBIDDEN

    actual_response = client_auth_header.post(
        url, data={"token": token_with_different_user_id}, format="json"
    )
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert expected_status_code == actual_response.status_code


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get_path_for_mock}",
    return_value=FAKE_SECRET,
)
def test_user_must_match_token_owner(
    mock_secret: MagicMock,
    client_auth_header: APIClient,
    valid_token: str,
):
    """
    Test that a valid JWT token allows the user to successfully log out (blacklist the token).
    """
    expected_detail_message = response_code_messages.LOGOUT_SUCCESSFUL["detail"]
    expected_code = response_code_messages.LOGOUT_SUCCESSFUL["code"]
    expected_status_code = status.HTTP_200_OK

    actual_response = client_auth_header.post(
        url, data={"token": valid_token}, format="json"
    )
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert expected_status_code == actual_response.status_code
