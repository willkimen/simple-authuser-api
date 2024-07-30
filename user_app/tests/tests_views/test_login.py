from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from user_app.constants import response_messages

User = get_user_model()

url: str = reverse("login")
JWT_SECRET_FOR_TESTS = "jwt_secret"


@pytest.fixture
def client() -> APIClient:
    """Returns an API client to make requests."""
    return APIClient()


@pytest.fixture
def data_nonexistent() -> dict[str:str]:
    """returns data for a non-existent user."""
    return {
        "email": "nonexistent@example.com",
        "password": "Password123!*",
    }


@pytest.fixture
def user_with_not_activated_account() -> User:
    """returns user instance without activated account"""
    user = User.objects.create_user(
        first_name="John",
        last_name="Doe",
        email="johndoe@email.com",
        password="Password1234!",
    )

    return user


@pytest.fixture
def user_with_activated_account() -> User:
    """returns user instance without activated account"""
    user = User.objects.create_user(
        first_name="John",
        last_name="Doe",
        email="johndoe@email.com",
        password="Password1234!",
        is_active=True,
    )

    return user


@pytest.mark.django_db
def test_nonexistent_user_is_not_logged_in(
    client: APIClient, data_nonexistent: dict[str, str]
):
    expected_message = response_messages.USER_NOT_FOUND
    expected_status_code = status.HTTP_404_NOT_FOUND

    response = client.post(url, data=data_nonexistent, format="json")

    assert expected_status_code == response.status_code
    assert expected_message == response.data["message"]


@pytest.mark.django_db
def test_user_with_not_activated_account_is_not_logged_in(
    user_with_not_activated_account: User,
    client: APIClient,
):
    expected_message = response_messages.USER_ACCOUNT_NOT_ACTIVATED
    expected_status_code = status.HTTP_403_FORBIDDEN

    response = client.post(
        url,
        data={
            "email": user_with_not_activated_account.email,
            "password": user_with_not_activated_account.password,
        },
        format="json",
    )

    assert expected_status_code == response.status_code
    assert expected_message == response.data["message"]


@pytest.mark.django_db
@patch("user_app.utils.jwt_token.os.environ.get", return_value=JWT_SECRET_FOR_TESTS)
def test_user_is_successfully_logged_in(
    mock_get,
    user_with_activated_account: User,
    client: APIClient,
):
    expected_status_code = status.HTTP_200_OK

    response = client.post(
        url,
        data={
            "email": user_with_activated_account.email,
            "password": user_with_activated_account.password,
        },
        format="json",
    )

    assert expected_status_code == response.status_code
    assert "access" in response.data
    assert "refresh" in response.data
