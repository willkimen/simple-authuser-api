"""
Module for testing the user account deletion functionality.
This module contains tests for the `delete` view of the user account API. 
The `delete` view allows authenticated users to delete their own accounts. 
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

from user_app.constants import response_codes_and_messages
from user_app.constants.path_for_mock import token_utils_module_path

# =========== Objects and constants ==============
User = get_user_model()
url: str = reverse("delete")
SECRET = "token_secret"
token_secret_mock = "settings.TOKEN_SECRET"
USER_ID = 100


# ============ Fixtures ================
@pytest.fixture
def user():
    """
    Provides a activated user object that is persisted in the database.
    """
    return User.objects.create_user(
        id=USER_ID,
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
        SECRET,
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


# ============ Tests ================
@pytest.mark.django_db
@patch(f"{token_utils_module_path}.{token_secret_mock}", SECRET)
def test_user_deletion_successful(client_auth_header: APIClient):
    """
    Tests that the user can successfully delete their own account.

    Args:
        client_auth_header (APIClient): API client with valid JWT authentication.
    """
    expected_status_code = status.HTTP_200_OK
    expected_code = response_codes_and_messages.USER_DELETED_SUCCESSFULLY["code"]
    expected_detail_message = response_codes_and_messages.USER_DELETED_SUCCESSFULLY[
        "detail"
    ]
    expected_user_delete = User.objects.get(id=USER_ID)

    actual_response = client_auth_header.delete(url)

    assert not User.objects.filter(
        id=expected_user_delete.id, email=expected_user_delete.email
    ).exists()
    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_status_code == actual_response.status_code
