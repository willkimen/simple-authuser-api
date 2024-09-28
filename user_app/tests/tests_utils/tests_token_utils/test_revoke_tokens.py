from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from user_app.constants.path_for_mock import token_utils_module_path
from user_app.models import BlacklistTokenModel, RefreshTokenModel
from user_app.utils.token_utils import revoke_tokens

# ========== Objects, auxiliary functions and constants ============
User = get_user_model()
SECRET = "fake_secret"
os_environ_get = "os.environ.get"
create_pair_token_mock = "create_pair_token"


def convert_unix_timestamp_to_aware_datetime(unix_timestamp: int) -> datetime:
    return timezone.make_aware(datetime.fromtimestamp(unix_timestamp))


# ============== Fixtures ==================
@pytest.fixture
def user() -> User:
    """
    Creates and returns a fake user to be used in tests.

    Returns:
        User: A Django user object with default attributes.
    """
    return User.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fake@email.com",
        password="FAKEpassword10!",
        is_active=True,
    )


@pytest.fixture
def access_payload(user: User) -> dict:
    """
    Creates and returns a fake access token payload simulating a JWT token payload.

    Args:
        user (User): The user associated with the access token.

    Returns:
        dict: Dictionary representing the access token payload with UID, type,
        JTI, and expiration.
    """
    return {
        "uid": user.id,
        "typ": "access",
        "jti": "fake_access_jti",
        "exp": int((timezone.now() + timedelta(seconds=60)).timestamp()),
    }


@pytest.fixture
def refresh_payload(user: User) -> dict:
    """
    Creates a refresh token and saves it in the database.

    Args:
        user (User): The user associated with the refresh token.

    Returns:
        dict: Dictionary representing the refresh token payload.
    """
    payload = {
        "uid": user.id,
        "typ": "refresh",
        "jti": "fake_refresh_jti",
        "exp": int((timezone.now() + timedelta(seconds=60)).timestamp()),
    }

    RefreshTokenModel.objects.create(
        user_id=payload["uid"],
        jti=payload["jti"],
        exp=payload["exp"],
    )

    return payload


@pytest.fixture
def expired_refresh_payload(user: User) -> dict:
    """
    Creates an expired refresh token and saves it in the database.

    Args:
        user (User): The user associated with the expired refresh token.

    Returns:
        dict: Dictionary representing the expired refresh token payload.
    """
    expired_payload = {
        "uid": user.id,
        "typ": "refresh",
        "jti": "fake_expired_refresh_jti",
        "exp": int((timezone.now() - timedelta(seconds=60)).timestamp()),
    }

    RefreshTokenModel.objects.create(
        user_id=expired_payload["uid"],
        jti=expired_payload["jti"],
        exp=expired_payload["exp"],
    )

    return expired_payload


@pytest.fixture
def refresh_payloads(user: User) -> list[dict]:
    """
    Creates a list of refresh tokens, some expired and others valid,
    and saves them in the database.

    Args:
        user (User): The user associated with the refresh tokens.

    Returns:
        list[dict]: List of dictionaries representing the refresh token payloads.
    """
    expired_date = int((timezone.now() - timedelta(seconds=60)).timestamp())
    date = int((timezone.now() + timedelta(seconds=60)).timestamp())

    payloads = [
        {
            "uid": user.id,
            "typ": "refresh",
            "jti": "jti_1",
            "exp": expired_date,
        },
        {
            "uid": user.id,
            "typ": "refresh",
            "jti": "jti_2",
            "exp": date,
        },
        {
            "uid": user.id,
            "typ": "refresh",
            "jti": "jti_3",
            "exp": expired_date,
        },
        {
            "uid": user.id,
            "typ": "refresh",
            "jti": "jti_4",
            "exp": date,
        },
    ]

    [
        RefreshTokenModel.objects.create(
            user_id=payload["uid"], jti=payload["jti"], exp=payload["exp"]
        )
        for payload in payloads
    ]

    return payloads


# ============= Tests ======================
@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
@patch(
    f"{token_utils_module_path}.{create_pair_token_mock}",
)
def test_access_token_persisted_in_blacklist(
    create_pair_token_mock: MagicMock, mock_secret: MagicMock, access_payload: dict
):
    """
    Tests if the access token is correctly added to the blacklist.

    Verifies:
    - That the access token has been persisted in the blacklist table.
    - That the function to create a new token pair was called.
    """
    access_payload["exp"] = convert_unix_timestamp_to_aware_datetime(
        access_payload["exp"]
    )

    revoke_tokens(access_payload["uid"], access_payload)

    assert BlacklistTokenModel.objects.filter(
        user_id=access_payload["uid"],
        typ=access_payload["typ"],
        jti=access_payload["jti"],
        exp=access_payload["exp"],
    ).exists()

    create_pair_token_mock.assert_called()


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
@patch(
    f"{token_utils_module_path}.{create_pair_token_mock}",
)
def test_refresh_token_persisted_in_blacklist(
    create_pair_token_mock: MagicMock,
    mock_secret: MagicMock,
    access_payload: dict,
    refresh_payload: dict,
):
    """
    Tests if the valid refresh token is added to the blacklist.

    Verifies:
    - That the refresh token has been persisted in the blacklist table.
    - That the function to create a new token pair was called.
    """
    refresh_payload["exp"] = convert_unix_timestamp_to_aware_datetime(
        refresh_payload["exp"]
    )

    revoke_tokens(access_payload["uid"], access_payload)

    assert BlacklistTokenModel.objects.filter(
        user_id=refresh_payload["uid"],
        typ=refresh_payload["typ"],
        jti=refresh_payload["jti"],
        exp=refresh_payload["exp"],
    ).exists()

    create_pair_token_mock.assert_called()


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
@patch(
    f"{token_utils_module_path}.{create_pair_token_mock}",
)
def test_expired_refresh_token_does_not_persisted_in_blacklist(
    create_pair_token_mock: MagicMock,
    mock_secret: MagicMock,
    access_payload: dict,
    expired_refresh_payload: RefreshTokenModel,
):
    """
    Tests if an expired refresh token is NOT added to the blacklist.

    Verifies:
    - That the expired refresh token has not been persisted in the blacklist table.
    - That the function to create a new token pair was called.
    """
    expired_refresh_payload["exp"] = convert_unix_timestamp_to_aware_datetime(
        expired_refresh_payload["exp"]
    )

    revoke_tokens(access_payload["uid"], access_payload)

    assert not BlacklistTokenModel.objects.filter(
        user_id=expired_refresh_payload["uid"],
        typ=expired_refresh_payload["typ"],
        jti=expired_refresh_payload["jti"],
        exp=expired_refresh_payload["exp"],
    ).exists()

    create_pair_token_mock.assert_called()


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
@patch(
    f"{token_utils_module_path}.{create_pair_token_mock}",
)
def test_all_refreshes_are_deleted(
    create_pair_token_mock: MagicMock,
    mock_secret: MagicMock,
    access_payload: dict,
    refresh_payloads: list[dict],
):
    """
    Tests if all refresh tokens are deleted after revocation.

    Verifies:
    - That all refresh tokens associated with the user have been removed
      from the database.
    - That the function to create a new token pair was called.
    """
    revoke_tokens(access_payload["uid"], access_payload)
    assert not RefreshTokenModel.objects.filter(
        user_id=access_payload["uid"],
    ).exists()

    create_pair_token_mock.assert_called()
