"""
Module for testing the account account deletion functionality.
This module contains tests for the `delete` view of the account API. 
The `delete` view allows authenticated accounts to delete their own accounts. 
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
from user_app.models.code import (
    AccountActivationCodeModel,
    ChangeEmailCodeModel,
    ResetPasswordCodeModel,
)
from user_app.models.token import BlacklistTokenModel, ValidTokenModel
from user_app.tests.constants import (
    FAKE_SECRET,
    TOKEN_SECRET_SETTING_TO_PATCH,
    TOKEN_SERVICE_MODULE_PATH,
    Account,
)

# =========== Objects and constants ==============
url: str = reverse("delete")
ACCOUNT_ID = 100


# ============ Fixtures ================
@pytest.fixture
def account():
    """
    Provides a activated account object that is persisted in the database.
    """
    return Account.objects.create_user(
        id=ACCOUNT_ID,
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fake@email.com",
        password="FAKEpassword10!",
        is_active=True,
    )


@pytest.fixture
def account_with_stored_verification_codes(account):
    """
    Fixture that associates a persisted account with verification codes stored
    in the database.

    Args:
        account: A persisted account instance from the database.

    Returns:
        account: The same account instance with associated verification codes.

    This fixture:
        - Creates an account activation code for the account.
        - Creates a change email verification code for the account.
        - Creates a password reset verification code for the account.
    """
    AccountActivationCodeModel.objects.create(account=account)
    ChangeEmailCodeModel.objects.create(account=account)
    ResetPasswordCodeModel.objects.create(account=account)
    return account


@pytest.fixture
def account_with_stored_tokens(account):
    """
    Fixture that associates a persisted account with valid and blacklisted tokens
    in the database.

    Args:
        account: A persisted account instance from the database.

    Returns:
        account: The same account instance with associated tokens.

    This fixture:
        - Creates a valid access token for the account and stores it in the database.
        - Creates a blacklisted token for the account and stores it in the database.
    """
    payload = {
        "typ": "access",
        "jti": "fake_valid_jti",
        "exp": int((timezone.now() + timedelta(seconds=60)).timestamp()),
    }

    ValidTokenModel.objects.create(account=account, **payload)
    payload["jti"] = "fake_valid_jti"
    BlacklistTokenModel.objects.create(account=account, **payload)

    return account


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


@pytest.fixture
def client_auth_header_with_stored_verification_codes(
    account_with_stored_verification_codes,
) -> APIClient:
    """
    Fixture that creates an authenticated API client with a token containing the ID
    of an account who has associated verification codes.

    Args:
        account_with_stored_verification_codes: A persisted account instance with stored
                                             verification codes.

    Returns:
        APIClient: An API client instance with authentication credentials set.

    This fixture:
        - Generates a JWT token with the account ID and other necessary claims.
        - Sets the token in the API client's authorization header.
        - Returns the authenticated API client for making requests.
    """

    token = jwt.encode(
        {
            "uid": account_with_stored_verification_codes.id,
            "typ": "access",
            "jti": "fake_jti",
            "exp": int((timezone.now() + timedelta(seconds=60)).timestamp()),
        },
        FAKE_SECRET,
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def client_auth_header_with_stored_tokens(
    account_with_stored_tokens,
) -> APIClient:
    """
    Fixture that creates an authenticated API client with a token containing the ID
    of an account who has associated stored tokens (valid and blacklisted tokens).

    Args:
        account_with_stored_tokens: A persisted account instance with stored tokens.

    Returns:
        APIClient: An API client instance with authentication credentials set.

    This fixture:
        - Generates a JWT token with the account ID and other necessary claims.
        - Sets the token in the API client's authorization header.
        - Returns the authenticated API client for making requests.
    """
    token = jwt.encode(
        {
            "uid": account_with_stored_tokens.id,
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
def test_account_deletion_successful(client_auth_header: APIClient):
    """
    Tests that the account can successfully delete their own account.

    Args:
        client_auth_header (APIClient): API client with valid JWT authentication.
    """
    expected_status_code = status.HTTP_200_OK
    expected_code = http_response.ACCOUNT_DELETED_SUCCESSFULLY["code"]
    expected_detail_message = http_response.ACCOUNT_DELETED_SUCCESSFULLY["detail"]
    expected_account_delete = Account.objects.get(id=ACCOUNT_ID)

    actual_response = client_auth_header.delete(url)

    assert not Account.objects.filter(
        id=expected_account_delete.id, email=expected_account_delete.email
    ).exists()
    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_status_code == actual_response.status_code


@pytest.mark.django_db
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_verification_codes_are_removed_when_account_is_deleted(
    client_auth_header_with_stored_verification_codes: APIClient,
):
    """
    Test that verifies the deletion of verification codes associated with an account when
    the account is deleted.

    This test:
        - Retrieves an account from the database and ensures the account exists along with
          their associated verification codes.
        - Sends a request to delete the account from the database.
        - Verifies that the account and all associated verification codes are
          deleted from the database.

    Args:
        client_auth_header_with_stored_verification_codes: Authenticated API client
                                                           with verification codes
                                                           associated with the account.

    The test ensures that deleting an account also removes the following associated
    verification codes:
        - Account activation code
        - Change email verification code
        - Reset password verification code
    """
    expected_account_delete = Account.objects.get(id=ACCOUNT_ID)

    assert Account.objects.filter(
        id=expected_account_delete.id, email=expected_account_delete.email
    ).exists()
    assert AccountActivationCodeModel.objects.filter(
        account=expected_account_delete
    ).exists()
    assert ChangeEmailCodeModel.objects.filter(account=expected_account_delete).exists()
    assert ResetPasswordCodeModel.objects.filter(
        account=expected_account_delete
    ).exists()

    client_auth_header_with_stored_verification_codes.delete(url)

    assert not Account.objects.filter(
        id=expected_account_delete.id, email=expected_account_delete.email
    ).exists()
    assert not AccountActivationCodeModel.objects.filter(
        account=expected_account_delete
    ).exists()
    assert not ChangeEmailCodeModel.objects.filter(
        account=expected_account_delete
    ).exists()
    assert not ResetPasswordCodeModel.objects.filter(
        account=expected_account_delete
    ).exists()


@pytest.mark.django_db
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_tokens_are_removed_when_account_is_deleted(
    client_auth_header_with_stored_tokens: APIClient,
):
    """
    Test that verifies the removal of tokens associated with an account when the account is deleted.

    This test:
        - Retrieves an account from the database and ensures the account exists along with their associated tokens.
        - Sends a request to delete the account from the database.
        - Verifies that the account and all associated tokens are deleted from the database.

    Args:
        client_auth_header_with_stored_tokens: Authenticated API client with tokens associated with the account.

    The test ensures that deleting an account also removes the following associated tokens:
        - Valid tokens
        - Blacklisted tokens
    """

    expected_account_delete = Account.objects.get(id=ACCOUNT_ID)

    assert Account.objects.filter(
        id=expected_account_delete.id, email=expected_account_delete.email
    ).exists()
    assert ValidTokenModel.objects.filter(account=expected_account_delete).exists()
    assert BlacklistTokenModel.objects.filter(account=expected_account_delete).exists()

    client_auth_header_with_stored_tokens.delete(url)

    assert not Account.objects.filter(
        id=expected_account_delete.id, email=expected_account_delete.email
    ).exists()
    assert not AccountActivationCodeModel.objects.filter(
        account=expected_account_delete
    ).exists()
    assert not ValidTokenModel.objects.filter(account=expected_account_delete).exists()
    assert not BlacklistTokenModel.objects.filter(
        account=expected_account_delete
    ).exists()
