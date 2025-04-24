"""
This module tests the login() view, which expects to receive a 
user's email and password, and returns a access and refresh JWT in the response."""

from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from user_app.constants import response_codes_and_messages
from user_app.tests.constants import (
    FAKE_SECRET,
    TOKEN_SECRET_SETTING_TO_PATCH,
    TOKEN_UTILS_MODULE_PATH,
    User,
)

# ========== Objects and constants ============
url: str = reverse("obtain_token_pair")
NONEXISTENT_EMAIL = "nonexistent@email.com"
USER_DATA = {
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
    return {"email": NONEXISTENT_EMAIL, "password": USER_DATA["password"]}


@pytest.fixture
def deactivated_user():
    """returns user instance without activated account"""
    return User.objects.create_user(**USER_DATA, is_active=False)


@pytest.fixture
def activated_user():
    """returns user instance without activated account"""
    return User.objects.create_user(**USER_DATA, is_active=True)


# =========== Tests ===================
@pytest.mark.django_db
def test_nonexistent_user_does_not_return_token_pair(
    client: APIClient, data_user_nonexistent: dict[str, str]
):
    """
    Test that attempting to log in with a nonexistent user does not return a JWT pair.

    Args:
        client (APIClient): The test client used to make HTTP requests.
        data_user_nonexistent (dict[str, str]): Dictionary containing login data for a user that does not exist.
    """
    expected_detail_message = response_codes_and_messages.USER_NOT_FOUND["detail"]
    expected_code = response_codes_and_messages.USER_NOT_FOUND["code"]
    expected_status_code = status.HTTP_404_NOT_FOUND

    actual_response = client.post(url, data=data_user_nonexistent, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
def test_user_with_not_activated_account_does_not_return_token_pair(
    deactivated_user, client: APIClient
):
    """
    Test that attempting to log in with an account that has not
    been activated does not return a JWT pair.

    Args:
        user_with_not_activated_account (User): A user instance with an account that
                                                is not activated.
        client (APIClient): The test client used to make HTTP requests.
    """
    expected_detail_message = response_codes_and_messages.USER_ACCOUNT_NOT_ACTIVATED[
        "detail"
    ]
    expected_code = response_codes_and_messages.USER_ACCOUNT_NOT_ACTIVATED["code"]
    expected_status_code = status.HTTP_403_FORBIDDEN

    actual_response = client.post(
        url,
        data={
            "email": deactivated_user.email,
            "password": deactivated_user.password,
        },
        format="json",
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_returns_token_pair_successfully(activated_user, client: APIClient):
    """
    Test that logging in with valid credentials for an activated
    account returns a JWT pair successfully.

    Args:
        user_with_activated_account (User): A user instance with an activated account.
        client (APIClient): The test client used to make HTTP requests.
    """
    expected_status_code = status.HTTP_200_OK
    expected_detail_message = response_codes_and_messages.LOGIN_SUCCESSFUL["detail"]
    expected_code = response_codes_and_messages.LOGIN_SUCCESSFUL["code"]

    actual_response = client.post(
        url,
        data={
            "email": activated_user.email,
            "password": activated_user.password,
        },
        format="json",
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert "access" and "refresh" in actual_response.data.keys()
