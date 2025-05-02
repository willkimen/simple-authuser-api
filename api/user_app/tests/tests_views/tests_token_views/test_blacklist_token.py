"""
Tests blacklist_token() view.  
"""

from datetime import timedelta
from unittest.mock import patch

import jwt
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from user_app.constants import authentication, http_response
from user_app.models import BlacklistTokenModel
from user_app.tests.constants import (
    FAKE_SECRET,
    TOKEN_SECRET_SETTING_TO_PATCH,
    TOKEN_UTILS_MODULE_PATH,
    Account,
)

# =========== Objects and constants ==============
url: str = reverse("blacklist_token")
UID = 1
UID_FOR_DIFFERENT_ACCOUNT = 100
JTI_FOR_AUTH = "fake_jti_for_auth_header"
JTI_IN_BLACKLIST = "fake_jti_in_blacklist"
INCORRECT_TYP = "incorrect_type"


# ============ Fixtures ================
@pytest.fixture
def account():
    """Generic account instance."""
    return Account.objects.create_user(
        id=UID,
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fake@email.com",
        password="FAKEpassword10!",
        is_active=True,
    )


@pytest.fixture
def payload(account) -> dict:
    """Generic payload."""
    return {
        "uid": account.id,
        "typ": "access",
        "jti": "fake_jti",
        "exp": int((timezone.now() + timedelta(seconds=60)).timestamp()),
    }


@pytest.fixture
def client_auth_header(payload: dict) -> APIClient:
    """
    Provides an API client with JWT authentication in the request header.

    Returns:
        APIClient: An API client with the Authorization header set to a valid JWT token.
    """
    payload["jti"] = JTI_FOR_AUTH
    token = jwt.encode(payload, FAKE_SECRET)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def blacklisted_token(payload: dict) -> str:
    """
    Creates and provides a blacklisted JWT token for testing.

    Returns:
        str: A JWT token that is blacklisted.
    """
    payload["jti"] = JTI_IN_BLACKLIST
    BlacklistTokenModel.objects.create(
        account_id=payload["uid"],
        jti=payload["jti"],
        typ=payload["typ"],
        exp=payload["exp"],
    )

    return jwt.encode(payload, FAKE_SECRET)


@pytest.fixture
def incorrect_typ_token(payload: dict) -> str:
    """
    Provides a JWT token with an incorrect type for testing.

    Returns:
        str: A JWT token with an incorrect type field ("typ").
    """
    payload["typ"] = INCORRECT_TYP
    return jwt.encode(payload, FAKE_SECRET)


@pytest.fixture
def token_with_different_account_id(payload: dict) -> str:
    """
    Provides a JWT token for a different account, to test token-account mismatches.

    Returns:
        str: A JWT token with an account ID different from the one making the request.
    """
    ACCOUNT_DATA = {
        "id": UID_FOR_DIFFERENT_ACCOUNT,
        "first_name": "fake_first_name",
        "last_name": "fake_last_name",
        "email": "fake2@email.com",
        "password": "FAKEpassword10!",
    }
    different_account = Account.objects.create_user(**ACCOUNT_DATA, is_active=True)
    payload["uid"] = different_account.id

    return jwt.encode(payload, FAKE_SECRET)


@pytest.fixture
def valid_token(payload: dict) -> str:
    """
    Provides a valid JWT token for testing.

    Returns:
        str: A valid JWT token for an active account.
    """

    return jwt.encode(payload, FAKE_SECRET)


# ========== Tests ================
@pytest.mark.django_db
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_token_already_in_blacklist(
    client_auth_header: APIClient, blacklisted_token: str
):
    """
    Test that a JWT token already blacklisted returns the appropriate error message.
    """
    expected_detail_message = authentication.TOKEN_IN_BLACKLIST["detail"]
    expected_code = authentication.TOKEN_IN_BLACKLIST["code"]
    expected_status_code = status.HTTP_403_FORBIDDEN

    actual_response = client_auth_header.post(
        url, data={"token": blacklisted_token}, format="json"
    )
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert expected_status_code == actual_response.status_code


@pytest.mark.django_db
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_token_type_must_be_access_or_refresh(
    client_auth_header: APIClient, incorrect_typ_token: str
):
    """
    Test that a JWT token with an incorrect type field ("typ") returns
    the appropriate error.
    """
    expected_detail_message = http_response.IS_NOT_ACCESS_OR_REFRESH_TOKEN["detail"]
    expected_code = http_response.IS_NOT_ACCESS_OR_REFRESH_TOKEN["code"]
    expected_status_code = status.HTTP_400_BAD_REQUEST

    actual_response = client_auth_header.post(
        url, data={"token": incorrect_typ_token}, format="json"
    )
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert expected_status_code == actual_response.status_code


@pytest.mark.django_db
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_user_must_match_token_owner(
    client_auth_header: APIClient, token_with_different_account_id: str
):
    """
    Test that a token's account ID must match the authenticated account's ID
    for the request to succeed.
    """
    expected_detail_message = http_response.ACCOUNT_TOKEN_MISMATCH["detail"]
    expected_code = http_response.ACCOUNT_TOKEN_MISMATCH["code"]
    expected_status_code = status.HTTP_403_FORBIDDEN

    actual_response = client_auth_header.post(
        url, data={"token": token_with_different_account_id}, format="json"
    )
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert expected_status_code == actual_response.status_code


@pytest.mark.django_db
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_logout_success_when_valid_token_is_provided(
    client_auth_header: APIClient, valid_token: str, payload: dict
):
    """
    Test that a valid JWT token allows the account to successfully log out (blacklist the token).
    """
    expected_detail_message = http_response.LOGOUT_SUCCESSFUL["detail"]
    expected_code = http_response.LOGOUT_SUCCESSFUL["code"]
    expected_status_code = status.HTTP_200_OK

    actual_response = client_auth_header.post(
        url, data={"token": valid_token}, format="json"
    )
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert expected_status_code == actual_response.status_code
    assert BlacklistTokenModel.objects.filter(jti=payload["jti"])
