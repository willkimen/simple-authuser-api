"""
This module tests the login() view, which expects to receive a 
account's email and password, and returns a access and refresh JWT in the response."""

from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from account_auth.constants import http_response
from account_auth.tests.constants import (
    FAKE_SECRET,
    TOKEN_SECRET_SETTING_TO_PATCH,
    TOKEN_SERVICE_MODULE_PATH,
    Account,
)

# ========== Objects and constants ============
url: str = reverse("obtain_token_pair")
NONEXISTENT_EMAIL = "nonexistent@email.com"
ACCOUNT_DATA = {
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
def data_account_nonexistent() -> dict[str:str]:
    """returns data for a non-existent account."""
    return {"email": NONEXISTENT_EMAIL, "password": ACCOUNT_DATA["password"]}


@pytest.fixture
def deactivated_account() -> None:
    """Persist an deactivated account."""
    Account.objects.create_user(**ACCOUNT_DATA, is_active=False)


@pytest.fixture
def activated_account() -> None:
    """Persist an activated account."""
    Account.objects.create_user(**ACCOUNT_DATA, is_active=True)


# =========== Tests ===================
@pytest.mark.django_db
def test_nonexistent_account_does_not_return_token_pair(
    client: APIClient, data_account_nonexistent: dict[str, str]
):
    """
    Test that attempting to log in with a nonexistent account does not return a JWT pair.

    Args:
        client (APIClient): The test client used to make HTTP requests.
        data_account_nonexistent (dict[str, str]): Dictionary containing login data for an account that does not exist.
    """
    expected_detail_message = http_response.ACCOUNT_NOT_FOUND["detail"]
    expected_code = http_response.ACCOUNT_NOT_FOUND["code"]
    expected_status_code = status.HTTP_404_NOT_FOUND

    actual_response = client.post(url, data=data_account_nonexistent, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
def test_account_with_not_activated_account_does_not_return_token_pair(
    deactivated_account: None, client: APIClient
):
    """
    Test that attempting to log in with an account that has not
    been activated does not return a JWT pair.

    Args:
        account_with_not_activated_account (Account): A account instance with an account that
                                                is not activated.
        client (APIClient): The test client used to make HTTP requests.
    """
    expected_detail_message = http_response.ACCOUNT_NOT_ACTIVATED["detail"]
    expected_code = http_response.ACCOUNT_NOT_ACTIVATED["code"]
    expected_status_code = status.HTTP_403_FORBIDDEN

    actual_response = client.post(
        url,
        data={
            "email": ACCOUNT_DATA["email"],
            "password": ACCOUNT_DATA["password"],
        },
        format="json",
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_returns_token_pair_successfully(activated_account: None, client: APIClient):
    """
    Test that logging in with valid credentials for an activated
    account returns a JWT pair successfully.

    Args:
        account_with_activated_account (Account): A activated account instance.
        client (APIClient): The test client used to make HTTP requests.
    """
    expected_status_code = status.HTTP_200_OK
    expected_detail_message = http_response.LOGIN_SUCCESSFUL["detail"]
    expected_code = http_response.LOGIN_SUCCESSFUL["code"]

    actual_response = client.post(
        url,
        data={
            "email": ACCOUNT_DATA["email"],
            "password": ACCOUNT_DATA["password"],
        },
        format="json",
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert "access" and "refresh" in actual_response.data.keys()
