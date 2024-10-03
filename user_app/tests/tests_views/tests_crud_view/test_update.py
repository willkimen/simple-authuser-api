"""
Tests for the update view in the user management module.
This module contains tests to ensure the correct functionality of the update view, 
which handles the partial update of user information for authenticated users.
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

from user_app.constants import response_codes_and_messages
from user_app.constants.path_for_mock import token_utils_module_path

# =========== Objects and constants ==============
User = get_user_model()
url: str = reverse("update")
SECRET = "token_secret"
os_environ_get = "os.environ.get"


# ============ Fixtures ================
@pytest.fixture
def client_auth_header() -> APIClient:
    """
    Provides an API client with JWT authentication in the request header.

    Returns:
        APIClient: An API client with the Authorization header set to a valid JWT token.
    """
    user = User.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fake@email.com",
        password="FAKEpassword10!",
        is_active=True,
    )
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
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
def test_update_first_name_successfully(
    token_secret_mock: MagicMock, client_auth_header: APIClient
):
    """
    Test that a user can successfully update their first name.
    """
    expected_status_code = status.HTTP_200_OK
    expected_code = response_codes_and_messages.USER_UPDATED_SUCCESSFULLY["code"]
    expected_detail_message = response_codes_and_messages.USER_UPDATED_SUCCESSFULLY["detail"]
    expected_new_first_name = "new_first_name"

    actual_response = client_auth_header.patch(
        url, data={"first_name": expected_new_first_name}, format="json"
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert expected_new_first_name == actual_response.data["user"]["first_name"]
    assert User.objects.filter(**actual_response.data["user"]).exists()


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
def test_update_last_name_successfully(
    token_secret_mock: MagicMock, client_auth_header: APIClient
):
    """
    Test that a user can successfully update their last name.
    """
    expected_status_code = status.HTTP_200_OK
    expected_code = response_codes_and_messages.USER_UPDATED_SUCCESSFULLY["code"]
    expected_detail_message = response_codes_and_messages.USER_UPDATED_SUCCESSFULLY["detail"]
    expected_new_last_name = "new_last_name"

    actual_response = client_auth_header.patch(
        url, data={"last_name": expected_new_last_name}, format="json"
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert expected_new_last_name == actual_response.data["user"]["last_name"]
    assert User.objects.filter(**actual_response.data["user"]).exists()


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
def test_update_first_and_last_name_successfully(
    token_secret_mock: MagicMock, client_auth_header: APIClient
):
    """
    Test that a user can successfully update both their first and last names.
    """
    expected_status_code = status.HTTP_200_OK
    expected_code = response_codes_and_messages.USER_UPDATED_SUCCESSFULLY["code"]
    expected_detail_message = response_codes_and_messages.USER_UPDATED_SUCCESSFULLY["detail"]
    expected_new_first_name = "new_first_name"
    expected_new_last_name = "new_last_name"

    actual_response = client_auth_header.patch(
        url,
        data={
            "first_name": expected_new_first_name,
            "last_name": expected_new_last_name,
        },
        format="json",
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert expected_new_first_name == actual_response.data["user"]["first_name"]
    assert expected_new_last_name == actual_response.data["user"]["last_name"]
    assert User.objects.filter(**actual_response.data["user"]).exists()
