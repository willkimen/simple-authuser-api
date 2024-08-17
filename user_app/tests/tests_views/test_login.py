"""
This module tests the login() view, which expects to receive a user's email and password,
and returns a access and refresh JWT in the response."""

from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from user_app.constants import response_code_messages

# ========== Objects and constants ============
User = get_user_model()
url: str = reverse("login")
JWT_SECRET_FOR_TESTS = "jwt_secret"
FAKE_NONEXISTENT_EMAIL = "nonexistent@email.com"
FAKE_USER_DATA = {
    "first_name": "fake_first_name",
    "last_name": "fake_last_name",
    "email": "fake@email.com",
    "password": "FAKEpassword10!",
}


# ============== Fixtures ==============
@pytest.fixture
def client() -> APIClient:
    """Returns an API client to make requests."""
    return APIClient()


@pytest.fixture
def data_user_nonexistent() -> dict[str:str]:
    """returns data for a non-existent user."""
    return {"email": FAKE_NONEXISTENT_EMAIL, "password": FAKE_USER_DATA["password"]}


@pytest.fixture
def user_with_not_activated_account() -> User:
    """returns user instance without activated account"""
    return User.objects.create_user(**FAKE_USER_DATA, is_active=False)


@pytest.fixture
def user_with_activated_account() -> User:
    """returns user instance without activated account"""
    return User.objects.create_user(**FAKE_USER_DATA, is_active=True)


# =========== Tests ===================
@pytest.mark.django_db
def test_nonexistent_user_is_not_logged_in(
    client: APIClient, data_user_nonexistent: dict[str, str]
):
    expected_detail_message = response_code_messages.USER_NOT_FOUND["detail"]
    expected_code = response_code_messages.USER_NOT_FOUND["code"]
    expected_status_code = status.HTTP_404_NOT_FOUND

    actual_response = client.post(url, data=data_user_nonexistent, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
def test_user_with_not_activated_account_is_not_logged_in(
    user_with_not_activated_account: User,
    client: APIClient,
):
    expected_detail_message = response_code_messages.USER_ACCOUNT_NOT_ACTIVATED[
        "detail"
    ]
    expected_code = response_code_messages.USER_ACCOUNT_NOT_ACTIVATED["code"]
    expected_status_code = status.HTTP_403_FORBIDDEN

    actual_response = client.post(
        url,
        data={
            "email": user_with_not_activated_account.email,
            "password": user_with_not_activated_account.password,
        },
        format="json",
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
@patch("user_app.utils.jwt_token.os.environ.get", return_value=JWT_SECRET_FOR_TESTS)
def test_user_is_successfully_logged_in(
    mock_get: MagicMock,
    user_with_activated_account: User,
    client: APIClient,
):
    expected_status_code = status.HTTP_200_OK
    expected_detail_message = response_code_messages.LOGIN_SUCCESSFUL["detail"]
    expected_code = response_code_messages.LOGIN_SUCCESSFUL["code"]

    actual_response = client.post(
        url,
        data={
            "email": user_with_activated_account.email,
            "password": user_with_activated_account.password,
        },
        format="json",
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert "access" and "refresh" in actual_response.data.keys()
