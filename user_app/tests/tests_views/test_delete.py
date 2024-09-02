"""
Module for testing the user account deletion functionality.
This module contains tests for the `delete` view of the user account API. The `delete` view allows authenticated users to delete their own accounts. 
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
from user_app.constants.path_for_mock import token_utils_module_path

# =========== Objects and constants ==============
User = get_user_model()
url: str = reverse("delete")
FAKE_SECRET = "token_secret"
os_environ_get_path_for_mock = "os.environ.get"


# ============ Fixtures ================
@pytest.fixture
def persisted_user() -> User:
    """
    Provides a user object that is persisted in the database.
    """
    return User.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fake@email.com",
        password="FAKEpassword10!",
        is_active=True,
    )


@pytest.fixture
def client_auth_header(persisted_user) -> APIClient:
    """
    Provides an API client with JWT authentication in the request header.

    Returns:
        APIClient: An API client with the Authorization header set to a valid JWT token.
    """
    token = jwt.encode(
        {
            "uid": persisted_user.id,
            "typ": "access",
            "jti": "fake_jti",
            "exp": int((datetime.now() + timedelta(seconds=60)).timestamp()),
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
def test_user_deletion_successful(
    token_secret_mock: MagicMock, client_auth_header: APIClient, persisted_user: User
):
    """
    Tests that the user can successfully delete their own account.

    Args:
        token_secret_mock (MagicMock): Mocked environment variable for JWT secret.
        client_auth_header (APIClient): API client with valid JWT authentication.
        persisted_user (User): The user to be deleted.
    """
    expected_status_code = status.HTTP_200_OK
    expected_code = response_code_messages.USER_DELETED_SUCCESSFULLY["code"]
    expected_detail_message = response_code_messages.USER_DELETED_SUCCESSFULLY["detail"]

    # Ensures the user exists in the database before the deletion request.
    assert User.objects.filter(
        id=persisted_user.id, email=persisted_user.email
    ).exists()

    actual_response = client_auth_header.delete(url)

    assert not User.objects.filter(
        id=persisted_user.id, email=persisted_user.email
    ).exists()
    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_status_code == actual_response.status_code
