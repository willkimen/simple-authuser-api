from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone
from account_auth.authentication.token_service import revoke_tokens
from account_auth.models import BlacklistTokenModel, ValidTokenModel
from account_auth.tests.constants import (
    CREATE_PAIR_TOKEN_FUNCTION_TO_PATCH,
    FAKE_SECRET,
    TOKEN_SECRET_SETTING_TO_PATCH,
    TOKEN_SERVICE_MODULE_PATH,
)


# ========== Objects, auxiliary functions and constants ============
def convert_unix_timestamp_to_aware_datetime(unix_timestamp: int) -> datetime:
    return timezone.make_aware(datetime.fromtimestamp(unix_timestamp))


# ============== Fixtures ==================
@pytest.fixture
def persisted_valid_payload(activated_account) -> dict:
    """
    Creates an token paylaod and saves it in the database.

    Args:
        account (Account): The account associated with the token.

    Returns:
        dict: Dictionary representing the token payload with UID, type,
        JTI, and expiration.
    """
    payload = {
        "uid": activated_account.id,
        "typ": "access",
        "jti": "fake_access_jti",
        "exp": int((timezone.now() + timedelta(seconds=60)).timestamp()),
    }

    ValidTokenModel.objects.create(
        account_id=payload["uid"],
        jti=payload["jti"],
        exp=payload["exp"],
        typ=payload["typ"],
    )

    return payload


@pytest.fixture
def expired_payload(activated_account) -> dict:
    """
    Creates an expired token payload and saves it in the database.

    Args:
        account (Account): The account associated with the expired token.

    Returns:
        dict: Dictionary representing the expired token payload.
    """
    expired_payload = {
        "uid": activated_account.id,
        "typ": "refresh",
        "jti": "fake_expired_refresh_jti",
        "exp": int((timezone.now() - timedelta(seconds=60)).timestamp()),
    }

    ValidTokenModel.objects.create(
        account_id=expired_payload["uid"],
        jti=expired_payload["jti"],
        exp=expired_payload["exp"],
        typ=expired_payload["typ"],
    )

    return expired_payload


@pytest.fixture
def payloads(activated_account) -> list[dict]:
    """
    Creates a list of tokens, some expired and others valid,
    and saves them in the database.

    Args:
        account (Account): The account associated with the tokens.

    Returns:
        list[dict]: List of dictionaries representing the token payloads.
    """
    expired_date = int((timezone.now() - timedelta(seconds=60)).timestamp())
    date = int((timezone.now() + timedelta(seconds=60)).timestamp())

    payloads = [
        {
            "uid": activated_account.id,
            "typ": "access",
            "jti": "jti_1",
            "exp": expired_date,
        },
        {
            "uid": activated_account.id,
            "typ": "access",
            "jti": "jti_2",
            "exp": date,
        },
        {
            "uid": activated_account.id,
            "typ": "refresh",
            "jti": "jti_3",
            "exp": expired_date,
        },
        {
            "uid": activated_account.id,
            "typ": "refresh",
            "jti": "jti_4",
            "exp": date,
        },
    ]

    [
        ValidTokenModel.objects.create(
            account_id=payload["uid"],
            jti=payload["jti"],
            exp=payload["exp"],
            typ=payload["typ"],
        )
        for payload in payloads
    ]

    return payloads


# ============= Tests ======================
@pytest.mark.django_db
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{CREATE_PAIR_TOKEN_FUNCTION_TO_PATCH}")
def test_token_persisted_in_blacklist(
    create_pair_token_function_mock: MagicMock, persisted_valid_payload: dict
):
    """
    Tests if the token is correctly added to the blacklist.

    Verifies:
    - That the token has been persisted in the blacklist table.
    - That the function to create a new token pair was called.
    """
    persisted_valid_payload["exp"] = convert_unix_timestamp_to_aware_datetime(
        persisted_valid_payload["exp"]
    )

    revoke_tokens(persisted_valid_payload["uid"])

    assert BlacklistTokenModel.objects.filter(
        account_id=persisted_valid_payload["uid"],
        typ=persisted_valid_payload["typ"],
        jti=persisted_valid_payload["jti"],
        exp=persisted_valid_payload["exp"],
    ).exists()

    create_pair_token_function_mock.assert_called()


@pytest.mark.django_db
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{CREATE_PAIR_TOKEN_FUNCTION_TO_PATCH}")
def test_expired_token_does_not_persisted_in_blacklist(
    create_pair_token_function_mock: MagicMock,
    persisted_valid_payload: dict,
    expired_payload: ValidTokenModel,
):
    """
    Tests if an expired token is NOT added to the blacklist.

    Verifies:
    - That the expired token has not been persisted in the blacklist table.
    - That the function to create a new token pair was called.
    """
    expired_payload["exp"] = convert_unix_timestamp_to_aware_datetime(
        expired_payload["exp"]
    )

    revoke_tokens(persisted_valid_payload["uid"])

    assert not BlacklistTokenModel.objects.filter(
        account_id=expired_payload["uid"],
        typ=expired_payload["typ"],
        jti=expired_payload["jti"],
        exp=expired_payload["exp"],
    ).exists()

    create_pair_token_function_mock.assert_called()


@pytest.mark.django_db
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{CREATE_PAIR_TOKEN_FUNCTION_TO_PATCH}")
def test_all_tokens_are_deleted(
    create_pair_token_function_mock: MagicMock,
    persisted_valid_payload: dict,
    payloads: list[dict],
):
    """
    Tests if all  tokens are deleted after revocation.

    Verifies:
    - That all tokens associated with the account have been removed
      from the database.
    - That the function to create a new token pair was called.
    """
    revoke_tokens(persisted_valid_payload["uid"])
    assert not ValidTokenModel.objects.filter(
        account_id=persisted_valid_payload["uid"],
    ).exists()

    create_pair_token_function_mock.assert_called()
