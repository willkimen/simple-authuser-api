"""
Tests for the update view in the account management module.
This module contains tests to ensure the correct functionality of the update view, 
which handles the partial update of account information for authenticated accounts.
"""

from datetime import timedelta
from unittest.mock import patch

import jwt
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from user_app.constants import http_response
from user_app.tests.constants import (
    FAKE_SECRET,
    TOKEN_SECRET_SETTING_TO_PATCH,
    TOKEN_SERVICE_MODULE_PATH,
    Account,
)

# =========== Objects and constants ==============
url: str = reverse("update")


# ============ Fixtures ================
@pytest.fixture
def client_auth_header() -> APIClient:
    """
    Provides an API client with JWT authentication in the request header.

    Returns:
        APIClient: An API client with the Authorization header set to a valid JWT token.
    """
    account = Account.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fake@email.com",
        password="FAKEpassword10!",
        is_active=True,
    )
    token = jwt.encode(
        {
            "uid": account.id,
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
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_update_first_name_successfully(client_auth_header: APIClient):
    """
    Test that an account can successfully update their first name.
    """
    expected_status_code = status.HTTP_200_OK
    expected_code = http_response.ACCOUNT_UPDATED_SUCCESSFULLY["code"]
    expected_detail_message = http_response.ACCOUNT_UPDATED_SUCCESSFULLY["detail"]
    expected_new_first_name = "new_first_name"

    actual_response = client_auth_header.patch(
        url, data={"first_name": expected_new_first_name}, format="json"
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert expected_new_first_name == actual_response.data["account"]["first_name"]
    assert Account.objects.filter(**actual_response.data["account"]).exists()


@pytest.mark.django_db
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_update_last_name_successfully(client_auth_header: APIClient):
    """
    Test that an account can successfully update their last name.
    """
    expected_status_code = status.HTTP_200_OK
    expected_code = http_response.ACCOUNT_UPDATED_SUCCESSFULLY["code"]
    expected_detail_message = http_response.ACCOUNT_UPDATED_SUCCESSFULLY["detail"]
    expected_new_last_name = "new_last_name"

    actual_response = client_auth_header.patch(
        url, data={"last_name": expected_new_last_name}, format="json"
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert expected_new_last_name == actual_response.data["account"]["last_name"]
    assert Account.objects.filter(**actual_response.data["account"]).exists()


@pytest.mark.django_db
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_update_first_and_last_name_successfully(client_auth_header: APIClient):
    """
    Test that an account can successfully update both their first and last names.
    """
    expected_status_code = status.HTTP_200_OK
    expected_code = http_response.ACCOUNT_UPDATED_SUCCESSFULLY["code"]
    expected_detail_message = http_response.ACCOUNT_UPDATED_SUCCESSFULLY["detail"]
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
    assert expected_new_first_name == actual_response.data["account"]["first_name"]
    assert expected_new_last_name == actual_response.data["account"]["last_name"]
    assert Account.objects.filter(**actual_response.data["account"]).exists()
