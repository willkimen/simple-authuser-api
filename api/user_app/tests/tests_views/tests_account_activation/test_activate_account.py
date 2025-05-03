"""
This module tests the activate_account() view, which aims to receive a activation 
code from the account via a POST request and activate their account.
For the account to have their account activated by the code, 
this code must exist in the database and be linked to the account's email.
"""

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from user_app.constants import http_response
from user_app.models import AccountActivationCodeModel, PendingAccountsModel
from user_app.tests.constants import (
    ACCOUNT_ACTIVATION_VIEWS_MODULE_PATH,
    ALLOW_REQUEST_FUNCTION_TO_PATCH,
    Account,
)

# ========== Objects and constants ============
url: str = reverse("activate_account")
CODE_NOT_EXISTS = "code_not_exists"


# ============ Fixture ================
@pytest.fixture
def deactivated_account():
    """Create a generic deactivated account."""
    return Account.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fake_email@email.com",
        password="FAKEpassword10!",
        is_active=False,
    )


@pytest.fixture
def expired_code(deactivated_account) -> str:
    """
    Creates a AccountActivationCodeModel instance with an
    expired date (24h + 1 minute ago compared to now)
    """

    account_activation_code = AccountActivationCodeModel.objects.create(
        account_id=deactivated_account.email,
    )

    # Create an expired date
    expired_date = account_activation_code.created_at - timedelta(minutes=1)

    # Changes the code creation date to an expired date and save
    account_activation_code.expires_at = expired_date
    account_activation_code.save()

    return account_activation_code.code


@pytest.fixture
def code_for_deactivated_account(deactivated_account) -> str:
    """
    This fixture creates AccountActivationCodeModel instance for account activation.

    Returns:
        dict: An activation code for activated account."""

    account_activation_code = AccountActivationCodeModel.objects.create(
        account_id=deactivated_account.email,
    )

    return account_activation_code.code


# ============ Tests ================
@pytest.mark.django_db
@patch(
    f"{ACCOUNT_ACTIVATION_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_successful_account_activation(
    allow_request_function_mock: MagicMock,
    client: APIClient,
    deactivated_account,
    code_for_deactivated_account: str,
):
    """
    Test if the account activation request successfully activates the account.

    Args:
        allow_request_function_mock (MagicMock): Mocked method to bypass rate limiting.
        deactivated_account (Account): An instance of a disabled account.
        code_for_deactivated_account: Code belonging to a deactivated account.
        client (APIClient): The API client used to make requests.
    """

    # Verify that the account is initially disabled.
    assert Account.objects.get(id=deactivated_account.id).is_active == False

    expected_detail_message = http_response.ACTIVATED_ACCOUNT["detail"]
    expected_code = http_response.ACTIVATED_ACCOUNT["code"]
    expected_status_code = status.HTTP_200_OK

    actual_response = client.post(
        url, data={"code": code_for_deactivated_account}, format="json"
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]

    # Verify that the account is activated
    assert Account.objects.get(id=deactivated_account.id).is_active == True


@pytest.mark.django_db
@patch(
    f"{ACCOUNT_ACTIVATION_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_successfully_activated_account_removes_the_code_in_the_database(
    allow_request_function_mock: MagicMock,
    client: APIClient,
    code_for_deactivated_account: str,
):
    """
    Test if the activation code is removed from the database after
    successful activation.

    Args:
        allow_request_function_mock (MagicMock): Mocked method to bypass rate limiting.
        deactivated_account (Account): An instance of a disabled account.
        code_for_deactivated_account: Code belonging to a deactivated account.
        client (APIClient): The API client used to make requests.
    """

    client.post(url, data={"code": code_for_deactivated_account}, format="json")

    # Assert that the activation code no longer exists in the database
    assert not AccountActivationCodeModel.objects.filter(
        code=code_for_deactivated_account
    ).exists()


@pytest.mark.django_db
@patch(
    f"{ACCOUNT_ACTIVATION_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_not_activate_account_when_expired_code(
    allow_request_function_mock: MagicMock, expired_code: str, client: APIClient
):
    """
    Test if the account activation request returns 410 when the
    provided code is expired.

    Args:
        allow_request_function_mock (MagicMock): Mocked throttle classes to bypass
                                                 rate limiting.
        expired_code (str): The expired activation code.
        client (APIClient): The API client used to make requests.

    This test checks that the server returns a 410 Gone status code and an appropriate
    error message when an expired activation code is provided in the request.
    """
    expected_detail_message = http_response.CODE_EXPIRED["detail"]
    expected_code = http_response.CODE_EXPIRED["code"]
    expected_status_code = status.HTTP_410_GONE

    actual_response = client.post(url, data={"code": expired_code}, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
@patch(
    f"{ACCOUNT_ACTIVATION_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_expired_code_is_removed_from_the_database(
    allow_request_function_mock: MagicMock, expired_code: str, client: APIClient
):
    """
    Test if the expired code is removed from the database when verified
    that it is expired.

    Args:
        allow_request_function_mock (MagicMock): Mocked throttle classes to bypass
                                           rate limiting.
        expired_code (str): The expired activation code.
        client (APIClient): The API client used to make requests.

    This test checks that an expired activation code is deleted from the database
    after an account activation attempt with the expired code.
    """
    client.post(url, data={"code": expired_code}, format="json")

    # Assert that the expired code no longer exists in the database
    assert not AccountActivationCodeModel.objects.filter(code=expired_code).exists()


@pytest.mark.django_db
@patch(
    f"{ACCOUNT_ACTIVATION_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_not_activate_account_when_code_field_does_not_exists(
    allow_request_function_mock: MagicMock, client: APIClient
):
    """
    Test if the account activation request returns 404 when
    the provided code does not exist.

    Args:
        allow_request_function_mock (MagicMock): Mocked throttle classes to bypass
                                           rate limiting.

        client (APIClient): The API client used to make requests.

    This test checks that the server returns a 404 Not Found status code
    and an appropriate error message when a non-existent activation code
    is provided in the request.
    """
    expected_detail_message = http_response.CODE_NOT_FOUND["detail"]
    expected_code = http_response.CODE_NOT_FOUND["code"]
    expected_status_code = status.HTTP_404_NOT_FOUND

    actual_response = client.post(url, data={"code": CODE_NOT_EXISTS}, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
def test_not_activate_account_when_request_limit_is_reached(client: APIClient):
    """
    Test if the account activation request is throttled when the
    request limit is reached.

    Args:
        client (APIClient): The API client used to make requests.

    This test ensures that the server returns a 429 Too Many Requests status code
    and the appropriate error message when the rate limit for account activation
    requests is exceeded.
    """

    expected_status_code = status.HTTP_429_TOO_MANY_REQUESTS
    expected_message = "Request was throttled."
    expected_error_code = "throttled"
    limit_exceeded = 6

    # Simulate multiple POST requests to exceed the rate limit
    for _ in range(limit_exceeded):
        actual_response = client.post(url)

    assert expected_status_code == actual_response.status_code
    assert expected_message in actual_response.data["detail"]
    assert expected_error_code == actual_response.data["code"]


@pytest.mark.django_db
@patch(
    f"{ACCOUNT_ACTIVATION_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_successfully_activated_account_removes_pending_account(
    allow_request_function_mock: MagicMock,
    client: APIClient,
    deactivated_account,
    code_for_deactivated_account: str,
):
    """
    Test if the PendingAccountsModel instance related to the account is removed
    after the account successfully activates their account.

    Args:
        allow_request_function_mock (MagicMock): Mocked method to bypass rate limiting.
        deactivated_account (Account): An instance of a disabled account.
        code_for_deactivated_account: Code belonging to a deactivated account.
        client (APIClient): The API client used to make requests.

    This test ensures that once the account successfully activates their account,
    their entry in the PendingAccountsModel table is removed from the database.
    """

    # Create a pending account entry for the deactivated account
    PendingAccountsModel.objects.create(account=deactivated_account)

    # Ensure the PendingAccountsModel entry exists before activation
    assert PendingAccountsModel.objects.filter(account=deactivated_account).exists()

    client.post(url, data={"code": code_for_deactivated_account}, format="json")

    # Verify that the PendingAccountsModel entry is removed after activation
    assert not PendingAccountsModel.objects.filter(account=deactivated_account).exists()
