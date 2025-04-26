from datetime import timedelta
from unittest.mock import patch

import jwt
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from user_app.constants import http_response, authentication
from user_app.models import BlacklistTokenModel
from user_app.tests.constants import (
    FAKE_SECRET,
    TOKEN_SECRET_SETTING_TO_PATCH,
    TOKEN_UTILS_MODULE_PATH,
    User,
)

# =========== Objects and constants ==============
url: str = reverse("verify_token")
FAKE_SECRET = "token_secret"
JTI_IN_BLACKLIST = "fake_jti_in_blacklist"
INCORRECT_TYP = "incorrect_type"


# ============ Fixtures ================
@pytest.fixture
def user():
    """Generic user instance."""
    return User.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fake@email.com",
        password="FAKEpassword10!",
        is_active=True,
    )


@pytest.fixture
def payload(user) -> dict:
    """Generic payload."""
    return {
        "uid": user.id,
        "typ": "access",
        "jti": "fake_jti",
        "exp": int((timezone.now() + timedelta(seconds=60)).timestamp()),
    }


@pytest.fixture
def client() -> APIClient:
    """
    Provides an API client in the request header.
    """
    return APIClient()


@pytest.fixture
def blacklisted_token(payload: dict) -> str:
    """
    Creates and provides a blacklisted JWT token for testing.

    Returns:
        str: A JWT token that is blacklisted.
    """
    payload["jti"] = JTI_IN_BLACKLIST
    BlacklistTokenModel.objects.create(
        user_id=payload["uid"],
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
def valid_token(payload: dict) -> str:
    """
    Provides a valid JWT token.
    """
    return jwt.encode(payload, FAKE_SECRET)


# ========== Tests ================
@pytest.mark.django_db
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_token_already_in_blacklist(client: APIClient, blacklisted_token: str):
    """
    Test that a JWT token already blacklisted returns the appropriate error message.
    """
    expected_detail_message = authentication.TOKEN_IN_BLACKLIST["detail"]
    expected_code = authentication.TOKEN_IN_BLACKLIST["code"]
    expected_status_code = status.HTTP_403_FORBIDDEN

    actual_response = client.post(url, data={"token": blacklisted_token}, format="json")

    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert expected_status_code == actual_response.status_code


@pytest.mark.django_db
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_token_type_must_be_access_or_refresh(
    client: APIClient, incorrect_typ_token: str
):
    """
    Test that a JWT token with an incorrect type field ("typ")
    returns the appropriate error.
    """
    expected_detail_message = (
        http_response.IS_NOT_ACCESS_OR_REFRESH_TOKEN["detail"]
    )
    expected_code = http_response.IS_NOT_ACCESS_OR_REFRESH_TOKEN["code"]
    expected_status_code = status.HTTP_400_BAD_REQUEST

    actual_response = client.post(
        url, data={"token": incorrect_typ_token}, format="json"
    )

    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert expected_status_code == actual_response.status_code


@pytest.mark.django_db
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_valid_token_successfully(client: APIClient, valid_token: str):
    """
    Tests if a valid token is processed successfully.

    Verifies that the response contains the correct message and code,
    and that the HTTP status is 200.
    """
    expected_detail_message = http_response.TOKEN_IS_VALID["detail"]
    expected_code = http_response.TOKEN_IS_VALID["code"]
    expected_status_code = status.HTTP_200_OK

    actual_response = client.post(url, data={"token": valid_token}, format="json")

    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert expected_status_code == actual_response.status_code
