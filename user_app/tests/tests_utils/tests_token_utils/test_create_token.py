from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from user_app.constants.path_for_mock import token_utils_module_path
from user_app.models import RefreshTokenModel
from user_app.utils.token_utils import create_token

# ========== Objects and constants ============
User = get_user_model()
SECRET = "fake_secret"
os_environ_get = "os.environ.get"
create_payload = "create_payload"


# ============== Fixture ==================
@pytest.fixture
def user() -> User:
    return User.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fakeemail@email.com",
        password="1344",
        is_active=True,
    )


@pytest.fixture
def payload(user: User) -> dict:
    return {
        "uid": user.id,
        "typ": "refresh",
        "jti": "fake_jti",
        "exp": int((timezone.now() + timedelta(seconds=60)).timestamp()),
    }


# ============= Tests ======================
@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
@patch(f"{token_utils_module_path}.{create_payload}")
def test_refresh_token_persisted_in_databas(
    mock_create_payload: MagicMock, mock_secret: MagicMock, payload: dict
):
    """
    Test if a refresh token is correctly persisted in the database.

    This test mocks the `create_payload` function to return a predefined payload and
    checks whether the corresponding refresh token is stored in the RefreshTokenModel.

    Args:
        mock_create_payload (MagicMock): Mocked version of the create_payload function.
        mock_secret (MagicMock): Mock a secret to create tokens, for testing.
        payload (dict): Mock the create_payload() function which is used internally
                        by the create_token() function, to return a fake payload.
    """
    # Mock a create payload function to return a default payload.
    mock_create_payload.return_value = payload

    create_token(user_id=payload["uid"], is_refresh=True)

    # Converte UNIX Timestamp date to aware datetime.
    payload["exp"] = timezone.make_aware(datetime.fromtimestamp(payload["exp"]))

    assert RefreshTokenModel.objects.filter(
        user_id=payload["uid"], jti=payload["jti"], exp=payload["exp"]
    ).exists()
