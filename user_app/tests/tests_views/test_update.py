"""
Tests for the update view in the user management module.
This module contains tests to ensure the correct functionality of the update view, which handles the partial update of user information for authenticated users.
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

# =========== Objects and constants ==============
User = get_user_model()
url: str = reverse("update")
FAKE_SECRET = "jwt_secret"


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
            "exp": int((datetime.now() + timedelta(seconds=60)).timestamp()),
        },
        FAKE_SECRET,
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


# ============ Tests ================
@pytest.mark.django_db
@patch("user_app.utils.jwt_token.os.environ.get", return_value=FAKE_SECRET)
def test_update_first_name_successfully(
    jwt_secret_mock: MagicMock, client_auth_header: APIClient
):
    """
    Test that a user can successfully update their first name.

    This test:
    - Uses the `client_auth_header` fixture to simulate an authenticated user.
    - Sends a PATCH request to the `update` endpoint with the new first name.
    - Asserts that the response status code is 200 OK.
    - Validates that the response message indicates a successful update.
    - Checks that the updated first name is reflected in the user data in the database.
    """
    expected_status_code = status.HTTP_200_OK
    expected_code = response_code_messages.USER_UPDATED_SUCCESSFULLY["code"]
    expected_detail_message = response_code_messages.USER_UPDATED_SUCCESSFULLY["detail"]
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
@patch("user_app.utils.jwt_token.os.environ.get", return_value=FAKE_SECRET)
def test_update_last_name_successfully(
    jwt_secret_mock: MagicMock, client_auth_header: APIClient
):
    """
    Test that a user can successfully update their last name.

    This test:
    - Uses the `client_auth_header` fixture to simulate an authenticated user.
    - Sends a PATCH request to the `update` endpoint with the new last name.
    - Asserts that the response status code is 200 OK.
    - Validates that the response message indicates a successful update.
    - Checks that the updated last name is reflected in the user data in the database.
    """
    expected_status_code = status.HTTP_200_OK
    expected_code = response_code_messages.USER_UPDATED_SUCCESSFULLY["code"]
    expected_detail_message = response_code_messages.USER_UPDATED_SUCCESSFULLY["detail"]
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
@patch("user_app.utils.jwt_token.os.environ.get", return_value=FAKE_SECRET)
def test_update_first_and_last_name_successfully(
    jwt_secret_mock: MagicMock, client_auth_header: APIClient
):
    """
    Test that a user can successfully update both their first and last names.

    This test:
    - Uses the `client_auth_header` fixture to simulate an authenticated user.
    - Sends a PATCH request to the `update` endpoint with new first and last names.
    - Asserts that the response status code is 200 OK.
    - Validates that the response message indicates a successful update.
    - Checks that the updated first and last names are reflected in the user data in the database.
    """
    expected_status_code = status.HTTP_200_OK
    expected_code = response_code_messages.USER_UPDATED_SUCCESSFULLY["code"]
    expected_detail_message = response_code_messages.USER_UPDATED_SUCCESSFULLY["detail"]
    expected_new_first_name = "new_first_name"
    expected_new_last_name = "new_last_name"

    actual_response = client_auth_header.patch(
        url,
        data={
            "first_name": expected_new_last_name,
            "last_name": expected_new_first_name,
        },
        format="json",
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert expected_new_first_name == actual_response.data["user"]["first_name"]
    assert expected_new_last_name == actual_response.data["user"]["last_name"]
    assert User.objects.filter(**actual_response.data["user"]).exists()
