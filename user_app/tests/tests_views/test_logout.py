"""
This module contains tests for the logout functionality of the user application.
It specifically verifies that a user's JWT (JSON Web Token) is successfully added 
to the blacklist when the user logs out, and that the appropriate response is returned.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import jwt
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from user_app.constants import response_code_messages
from user_app.models import JWTBlackList

# ============== Objects and constants ==============
User = get_user_model()
url: str = reverse("logout")
FAKE_SECRET = "fake_secret"


# ============== Fixtures ================
@pytest.fixture
def user() -> User:
    return User.objects.create_user(
        email="fakeemail@email.com",
        first_name="fake",
        last_name="fake",
        password="FAKEfake10!",
        is_active=True,
    )


@pytest.fixture
def fake_payload(user: User) -> dict:
    return {
        "uid": user.id,
        "typ": "fake_typ",
        "jti": "fake_jti",
        "exp": int((datetime.now() + timedelta(days=1)).timestamp()),
    }


@pytest.fixture
def token(fake_payload: dict) -> str:
    return jwt.encode(fake_payload, FAKE_SECRET)


@pytest.fixture
def client_with_auth_header(token: str) -> APIClient:
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


# ================ Tests ==================
@pytest.mark.django_db
@patch("user_app.utils.jwt_token.os.environ.get", return_value=FAKE_SECRET)
def test_user_logout_successful(
    mock_jwt_secret: MagicMock, client_with_auth_header: APIClient, fake_payload: str
):
    expected_detail_message = response_code_messages.LOGOUT_SUCCESSFUL["detail"]
    expected_code = response_code_messages.LOGOUT_SUCCESSFUL["code"]
    expected_status_code = status.HTTP_200_OK

    response_actual = client_with_auth_header.post(url)

    assert expected_status_code == response_actual.status_code
    assert expected_detail_message == response_actual.data["detail"]
    assert expected_code == response_actual.data["code"]
    assert JWTBlackList.objects.filter(jti=fake_payload["jti"]).exists()
