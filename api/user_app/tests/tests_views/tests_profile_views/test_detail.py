"""
Test Module: detail() View

This module contains the tests for the `detail` API view, 
which retrieves the details of an authenticated account. 
The tests ensure that the authenticated account receives their 
correct data in the response.
"""

from datetime import timedelta
from unittest.mock import patch

import jwt
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from user_app.tests.constants import (
    FAKE_SECRET,
    TOKEN_SECRET_SETTING_TO_PATCH,
    TOKEN_UTILS_MODULE_PATH,
    Account,
)

# =========== Objects and constants ==============
url: str = reverse("detail")


# ============ Fixtures ================
@pytest.fixture
def account():
    return Account.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fake@email.com",
        password="FAKEpassword10!",
        is_active=True,
    )


@pytest.fixture
def client_auth_header(account) -> APIClient:
    """
    Provides an API client with JWT authentication in the request header.

    Returns:
        APIClient: An API client with the Authorization header set to a valid JWT token.
    """
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
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_logged_account_returns_their_data_successfully(
    client_auth_header: APIClient, account
):
    """
    This test verifies that an authenticated account can successfully retrieve their own
    details via the `detail` API view.
    """
    expected_status_code = status.HTTP_200_OK

    actual_response = client_auth_header.get(url)

    assert Account.objects.filter(**actual_response.data["account"]).exists()
    assert account.id == actual_response.data["account"]["id"]
    assert account.first_name == actual_response.data["account"]["first_name"]
    assert account.last_name == actual_response.data["account"]["last_name"]
    assert account.email == actual_response.data["account"]["email"]
    assert account.is_active == actual_response.data["account"]["is_active"]
    assert expected_status_code == actual_response.status_code
