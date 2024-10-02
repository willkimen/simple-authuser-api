from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from user_app.constants.path_for_mock import token_utils_module_path
from user_app.models import BlacklistTokenModel, ValidTokenModel
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
def payload(user: User) -> dict:
    """
    Creates an token paylaod and saves it in the database.

    Args:
        user (User): The user associated with the token.

    Returns:
        dict: Dictionary representing the token payload with UID, type,
        JTI, and expiration.
    """
    payload = {
        "uid": user.id,
        "typ": "access",
        "jti": "fake_access_jti",
        "exp": int((timezone.now() + timedelta(seconds=60)).timestamp()),
    }

    ValidTokenModel.objects.create(
        user_id=payload["uid"],
        jti=payload["jti"],
        exp=payload["exp"],
        typ=payload["typ"],
    )

    return payload


@pytest.fixture
def expired_payload(user: User) -> dict:
    """
    Creates an expired token payload and saves it in the database.

    Args:
        user (User): The user associated with the expired token.

    Returns:
        dict: Dictionary representing the expired token payload.
    """
    expired_payload = {
        "uid": user.id,
        "typ": "refresh",
        "jti": "fake_expired_refresh_jti",
        "exp": int((timezone.now() - timedelta(seconds=60)).timestamp()),
    }

    ValidTokenModel.objects.create(
        user_id=expired_payload["uid"],
        jti=expired_payload["jti"],
        exp=expired_payload["exp"],
        typ=expired_payload["typ"],
    )

    return expired_payload


@pytest.fixture
def payloads(user: User) -> list[dict]:
    """
    Creates a list of tokens, some expired and others valid,
    and saves them in the database.

    Args:
        user (User): The user associated with the tokens.

    Returns:
        list[dict]: List of dictionaries representing the token payloads.
    """
    expired_date = int((timezone.now() - timedelta(seconds=60)).timestamp())
    date = int((timezone.now() + timedelta(seconds=60)).timestamp())

    payloads = [
        {
            "uid": user.id,
            "typ": "access",
            "jti": "jti_1",
            "exp": expired_date,
        },
        {
            "uid": user.id,
            "typ": "access",
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
        ValidTokenModel.objects.create(
            user_id=payload["uid"],
            jti=payload["jti"],
            exp=payload["exp"],
            typ=payload["typ"],
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
def test_token_persisted_in_blacklist(
    create_pair_token_mock: MagicMock, mock_secret: MagicMock, payload: dict
):
    """
    Tests if the token is correctly added to the blacklist.

    Verifies:
    - That the token has been persisted in the blacklist table.
    - That the function to create a new token pair was called.
    """
    payload["exp"] = convert_unix_timestamp_to_aware_datetime(payload["exp"])

    revoke_tokens(payload["uid"])

    assert BlacklistTokenModel.objects.filter(
        user_id=payload["uid"],
        typ=payload["typ"],
        jti=payload["jti"],
        exp=payload["exp"],
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
def test_expired_token_does_not_persisted_in_blacklist(
    create_pair_token_mock: MagicMock,
    mock_secret: MagicMock,
    payload: dict,
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

    revoke_tokens(payload["uid"])

    assert not BlacklistTokenModel.objects.filter(
        user_id=expired_payload["uid"],
        typ=expired_payload["typ"],
        jti=expired_payload["jti"],
        exp=expired_payload["exp"],
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
def test_all_tokens_are_deleted(
    create_pair_token_mock: MagicMock,
    mock_secret: MagicMock,
    payload: dict,
    payloads: list[dict],
):
    """
    Tests if all  tokens are deleted after revocation.

    Verifies:
    - That all tokens associated with the user have been removed
      from the database.
    - That the function to create a new token pair was called.
    """
    revoke_tokens(payload["uid"])
    assert not ValidTokenModel.objects.filter(
        user_id=payload["uid"],
    ).exists()

    create_pair_token_mock.assert_called()
