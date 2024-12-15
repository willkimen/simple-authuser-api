from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone
from user_app.models import ValidTokenModel
from user_app.tests.constants import (
    CREATE_PAYLOAD_FUNCTION_TO_PATCH,
    FAKE_SECRET,
    TOKEN_SECRET_SETTING_TO_PATCH,
    TOKEN_UTILS_MODULE_PATH,
)
from user_app.utils.token_utils import create_token


# ============= Tests ======================
@pytest.mark.django_db
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{CREATE_PAYLOAD_FUNCTION_TO_PATCH}")
def test_token_persisted_in_database(
    create_payload_function_mock: MagicMock, payload: dict
):
    """
    Test if a token is correctly persisted in the database.

    This test mocks the `create_payload` function to return a predefined payload and
    checks whether the corresponding token is stored in the ValidTokenModel.

    Args:
        create_payload_function_mock (MagicMock): Mocked version of the
                                                  create_payload function.
        payload (dict): Mock the create_payload() function which is used internally
                        by the create_token() function, to return a fake payload.
    """
    # Mock a create payload function to return a default payload.
    create_payload_function_mock.return_value = payload

    create_token(user_id=payload["uid"], is_refresh=True)

    # Converte UNIX Timestamp date to aware datetime.
    payload["exp"] = timezone.make_aware(datetime.fromtimestamp(payload["exp"]))

    assert ValidTokenModel.objects.filter(
        user_id=payload["uid"],
        jti=payload["jti"],
        exp=payload["exp"],
        typ=payload["typ"],
    ).exists()
