"""
Module for testing the user account deletion functionality.
This module contains tests for the `delete` view of the user account API. 
The `delete` view allows authenticated users to delete their own accounts. 
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
from user_app.models.code_models import (
    AccountActivationCodeModel,
    ChangeEmailCodeModel,
    ResetPasswordCodeModel,
)
from user_app.models.token_models import BlacklistTokenModel, ValidTokenModel
from user_app.tests.constants import (
    FAKE_SECRET,
    TOKEN_SECRET_SETTING_TO_PATCH,
    TOKEN_UTILS_MODULE_PATH,
    User,
)

# =========== Objects and constants ==============
url: str = reverse("delete")
USER_ID = 100


# ============ Fixtures ================
@pytest.fixture
def user():
    """
    Provides a activated user object that is persisted in the database.
    """
    return User.objects.create_user(
        id=USER_ID,
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fake@email.com",
        password="FAKEpassword10!",
        is_active=True,
    )


@pytest.fixture
def user_with_stored_verification_codes(user):
    """
    Fixture that associates a persisted user with verification codes stored
    in the database.

    Args:
        user: A persisted user instance from the database.

    Returns:
        user: The same user instance with associated verification codes.

    This fixture:
        - Creates an account activation code for the user.
        - Creates a change email verification code for the user.
        - Creates a password reset verification code for the user.
    """
    AccountActivationCodeModel.objects.create(user=user)
    ChangeEmailCodeModel.objects.create(user=user)
    ResetPasswordCodeModel.objects.create(user=user)
    return user


@pytest.fixture
def user_with_stored_tokens(user):
    """
    Fixture that associates a persisted user with valid and blacklisted tokens
    in the database.

    Args:
        user: A persisted user instance from the database.

    Returns:
        user: The same user instance with associated tokens.

    This fixture:
        - Creates a valid access token for the user and stores it in the database.
        - Creates a blacklisted token for the user and stores it in the database.
    """
    payload = {
        "typ": "access",
        "jti": "fake_valid_jti",
        "exp": int((timezone.now() + timedelta(seconds=60)).timestamp()),
    }

    ValidTokenModel.objects.create(user=user, **payload)
    payload["jti"] = "fake_valid_jti"
    BlacklistTokenModel.objects.create(user=user, **payload)

    return user


@pytest.fixture
def client_auth_header(user) -> APIClient:
    """
    Provides an API client with JWT authentication in the request header.

    Returns:
        APIClient: An API client with the Authorization header set to a valid JWT token.
    """
    token = jwt.encode(
        {
            "uid": user.id,
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
    user_with_stored_verification_codes,
) -> APIClient:
    """
    Fixture that creates an authenticated API client with a token containing the ID
    of a user who has associated verification codes.

    Args:
        user_with_stored_verification_codes: A persisted user instance with stored
                                             verification codes.

    Returns:
        APIClient: An API client instance with authentication credentials set.

    This fixture:
        - Generates a JWT token with the user ID and other necessary claims.
        - Sets the token in the API client's authorization header.
        - Returns the authenticated API client for making requests.
    """

    token = jwt.encode(
        {
            "uid": user_with_stored_verification_codes.id,
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
    user_with_stored_tokens,
) -> APIClient:
    """
    Fixture that creates an authenticated API client with a token containing the ID
    of a user who has associated stored tokens (valid and blacklisted tokens).

    Args:
        user_with_stored_tokens: A persisted user instance with stored tokens.

    Returns:
        APIClient: An API client instance with authentication credentials set.

    This fixture:
        - Generates a JWT token with the user ID and other necessary claims.
        - Sets the token in the API client's authorization header.
        - Returns the authenticated API client for making requests.
    """
    token = jwt.encode(
        {
            "uid": user_with_stored_tokens.id,
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
def test_user_deletion_successful(client_auth_header: APIClient):
    """
    Tests that the user can successfully delete their own account.

    Args:
        client_auth_header (APIClient): API client with valid JWT authentication.
    """
    expected_status_code = status.HTTP_200_OK
    expected_code = http_response.USER_DELETED_SUCCESSFULLY["code"]
    expected_detail_message = http_response.USER_DELETED_SUCCESSFULLY[
        "detail"
    ]
    expected_user_delete = User.objects.get(id=USER_ID)

    actual_response = client_auth_header.delete(url)

    assert not User.objects.filter(
        id=expected_user_delete.id, email=expected_user_delete.email
    ).exists()
    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_status_code == actual_response.status_code


@pytest.mark.django_db
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_verification_codes_are_removed_when_user_is_deleted(
    client_auth_header_with_stored_verification_codes: APIClient,
):
    """
    Test that verifies the deletion of verification codes associated with a user when
    the user is deleted.

    This test:
        - Retrieves a user from the database and ensures the user exists along with
          their associated verification codes.
        - Sends a request to delete the user from the database.
        - Verifies that the user and all associated verification codes are
          deleted from the database.

    Args:
        client_auth_header_with_stored_verification_codes: Authenticated API client
                                                           with verification codes
                                                           associated with the user.

    The test ensures that deleting a user also removes the following associated
    verification codes:
        - Account activation code
        - Change email verification code
        - Reset password verification code
    """
    expected_user_delete = User.objects.get(id=USER_ID)

    assert User.objects.filter(
        id=expected_user_delete.id, email=expected_user_delete.email
    ).exists()
    assert AccountActivationCodeModel.objects.filter(user=expected_user_delete).exists()
    assert ChangeEmailCodeModel.objects.filter(user=expected_user_delete).exists()
    assert ResetPasswordCodeModel.objects.filter(user=expected_user_delete).exists()

    client_auth_header_with_stored_verification_codes.delete(url)

    assert not User.objects.filter(
        id=expected_user_delete.id, email=expected_user_delete.email
    ).exists()
    assert not AccountActivationCodeModel.objects.filter(
        user=expected_user_delete
    ).exists()
    assert not ChangeEmailCodeModel.objects.filter(user=expected_user_delete).exists()
    assert not ResetPasswordCodeModel.objects.filter(user=expected_user_delete).exists()


@pytest.mark.django_db
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_tokens_are_removed_when_user_is_deleted(
    client_auth_header_with_stored_tokens: APIClient,
):
    """
    Test that verifies the removal of tokens associated with a user when the user is deleted.

    This test:
        - Retrieves a user from the database and ensures the user exists along with their associated tokens.
        - Sends a request to delete the user from the database.
        - Verifies that the user and all associated tokens are deleted from the database.

    Args:
        client_auth_header_with_stored_tokens: Authenticated API client with tokens associated with the user.

    The test ensures that deleting a user also removes the following associated tokens:
        - Valid tokens
        - Blacklisted tokens
    """

    expected_user_delete = User.objects.get(id=USER_ID)

    assert User.objects.filter(
        id=expected_user_delete.id, email=expected_user_delete.email
    ).exists()
    assert ValidTokenModel.objects.filter(user=expected_user_delete).exists()
    assert BlacklistTokenModel.objects.filter(user=expected_user_delete).exists()

    client_auth_header_with_stored_tokens.delete(url)

    assert not User.objects.filter(
        id=expected_user_delete.id, email=expected_user_delete.email
    ).exists()
    assert not AccountActivationCodeModel.objects.filter(
        user=expected_user_delete
    ).exists()
    assert not ValidTokenModel.objects.filter(user=expected_user_delete).exists()
    assert not BlacklistTokenModel.objects.filter(user=expected_user_delete).exists()
