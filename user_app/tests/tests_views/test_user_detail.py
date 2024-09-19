"""
Test Module: user_detail() View

This module contains the tests for the `user_detail` API view, which retrieves the details
of an authenticated user. The tests ensure that the authenticated user receives their
correct data in the response.
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

from user_app.constants.path_for_mock import token_utils_module_path

# =========== Objects and constants ==============
User = get_user_model()
url: str = reverse("detail")
FAKE_SECRET = "token_secret"
os_environ_get_path_for_mock = "os.environ.get"


# ============ Fixtures ================
@pytest.fixture
def user() -> User:
    return User.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fake@email.com",
        password="FAKEpassword10!",
        is_active=True,
    )


@pytest.fixture
def client_auth_header(user) -> APIClient:
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
@patch(
    f"{token_utils_module_path}.{os_environ_get_path_for_mock}",
    return_value=FAKE_SECRET,
)
def test_logged_user_returns_their_data_successfully(
    token_secret_mock: MagicMock, client_auth_header: APIClient, user: User
):
    """
    This test verifies that an authenticated user can successfully retrieve their own
    details via the `user_detail` API view.
    """
    expected_status_code = status.HTTP_200_OK

    actual_response = client_auth_header.get(url)

    assert User.objects.filter(**actual_response.data["user"]).exists()
    assert user.id == actual_response.data["user"]["id"]
    assert user.first_name == actual_response.data["user"]["first_name"]
    assert user.last_name == actual_response.data["user"]["last_name"]
    assert user.email == actual_response.data["user"]["email"]
    assert user.is_active == actual_response.data["user"]["is_active"]
    assert expected_status_code == actual_response.status_code
