"""
This module tests the check_token() function, which takes a JWT as an argument and returns the payload. It tests all possible exceptions raised as well as the success scenario.
"""

import base64
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import jwt
import pytest

from user_app.constants import token_exception_messages
from user_app.constants.path_for_mock import token_utils_module_path
from user_app.exceptions import (
    DecodeException,
    ExpiredSignatureException,
    InvalidAlgorithmException,
    InvalidSignatureException,
    JWTBlackListException,
)
from user_app.models import JWTBlackList
from user_app.utils.token_utils import check_token

# ========== Objects and constants ============
FAKE_SECRET = "fake_secret"
INVALID_SECRET = "invalid_secret"
MALFORMED_TOKEN = "malformed.token.string"
os_environ_get_path_for_mock = "os.environ.get"


# ============== Fixture ==================
@pytest.fixture
def fake_payload() -> dict:
    return {
        "uid": 10,
        "typ": "fake_jti",
        "jti": "fake_jti",
        "exp": int((datetime.now() + timedelta(seconds=60)).timestamp()),
    }


@pytest.fixture
def token_expired(fake_payload: dict) -> str:
    """
    Fixture that creates an expired JWT for testing purposes.

    Returns:
        str: The expired JWT.
    """
    fake_payload["exp"] = int((datetime.now() - timedelta(seconds=60)).timestamp())

    return jwt.encode(fake_payload, FAKE_SECRET)


@pytest.fixture
def token_with_invalid_secret(fake_payload: dict) -> str:
    """
    Fixture that creates a JWT with an invalid secret for testing purposes.

    Returns:
        str: The JWT with an invalid secret.
    """
    return jwt.encode(fake_payload, INVALID_SECRET)


@pytest.fixture
def token_malformed() -> str:
    """
    Fixture that creates a malformed JWT for testing purposes.

    Returns:
        str: The malformed JWT.
    """
    return MALFORMED_TOKEN


@pytest.fixture
def token(fake_payload: dict) -> str:
    """
    Fixture that creates a valid JWT for testing purposes.

    Returns:
        str: The valid JWT.
    """
    return jwt.encode(fake_payload, FAKE_SECRET)


@pytest.fixture
def token_with_invalid_algorithm(fake_payload: dict) -> str:
    """
    Fixture that creates a JWT with an invalid algorithm for testing purposes.

    Returns:
        str: The JWT with an invalid algorithm.
    """
    # Encode the payload into a JWT token with the correct secret
    token = jwt.encode(fake_payload, FAKE_SECRET)

    # Split the token into its components: header, payload, and signature
    header, payload, signature = token.split(".")

    # Decode the header from Base64 URL safe format
    header_data = json.loads(base64.urlsafe_b64decode(header + "==").decode("utf-8"))

    # Modify the algorithm in the header to an invalid one (RS256)
    header_data["alg"] = "RS256"  # Invalid algorithm

    # Re-encode the modified header into Base64 URL safe format
    modified_header = (
        base64.urlsafe_b64encode(json.dumps(header_data).encode("utf-8"))
        .decode("utf-8")
        .rstrip("=")
    )

    # Reassemble the token with the modified header
    return f"{modified_header}.{payload}.{signature}"


# ============= Tests ======================
@patch(
    f"{token_utils_module_path}.{os_environ_get_path_for_mock}",
    return_value=FAKE_SECRET,
)
def test_expired_token(token_secret_mock: MagicMock, token_expired: str):
    """
    Test if the function raises ExpiredSignatureError when the token is expired.

    Args:
        token_secret_mock: Mocked environment variable for JWT secret.
        token_expired (str): The expired JWT.
    """
    expected_dict_with_code_and_detail = token_exception_messages.EXPIRED_SIGNATURE
    with pytest.raises(ExpiredSignatureException) as e:
        check_token(token_expired)

    assert expected_dict_with_code_and_detail == e.value.dict_repr()


@patch(
    f"{token_utils_module_path}.{os_environ_get_path_for_mock}",
    return_value=FAKE_SECRET,
)
def test_invalid_signature(
    token_secret_mock: MagicMock, token_with_invalid_secret: str
):
    """
    Test if the function raises InvalidSignatureError when the token has an invalid signature.

    Args:
        token_secret_mock: Mocked environment variable for JWT secret.
        token_with_invalid_secret (str): The JWT with an incorrect secret.
    """
    expected_dict_with_code_and_detail = token_exception_messages.INVALID_SIGNATURE
    with pytest.raises(InvalidSignatureException) as e:
        check_token(token_with_invalid_secret)

    assert expected_dict_with_code_and_detail == e.value.dict_repr()


@patch(
    f"{token_utils_module_path}.{os_environ_get_path_for_mock}",
    return_value=FAKE_SECRET,
)
def test_decode_error(token_secret_mock: MagicMock, token_malformed: str):
    """
    Test if the function raises DecodeError when the token is malformed.

    Args:
        token_secret_mock: Mocked environment variable for JWT secret.
        token_malformed (str): The malformed JWT.
    """
    expected_dict_with_code_and_detail = token_exception_messages.DECODE_ERROR
    with pytest.raises(DecodeException) as e:
        check_token(token_malformed)

    assert expected_dict_with_code_and_detail == e.value.dict_repr()


@patch(
    f"{token_utils_module_path}.{os_environ_get_path_for_mock}",
    return_value=FAKE_SECRET,
)
def test_invalid_algorithm(
    token_secret_mock: MagicMock, token_with_invalid_algorithm: str
):
    """
    Test if the function raises InvalidAlgorithmError when the token has an invalid algorithm.

    Args:
        token_secret_mock: Mocked environment variable for JWT secret.
        token_with_invalid_algorithm (str): The JWT with an invalid algorithm.
    """
    expected_dict_with_code_and_detail = token_exception_messages.INVALID_ALGORITHM
    with pytest.raises(InvalidAlgorithmException) as e:
        check_token(token_with_invalid_algorithm)

    assert expected_dict_with_code_and_detail == e.value.dict_repr()


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get_path_for_mock}",
    return_value=FAKE_SECRET,
)
def test_token_in_black_list(token_secret_mock: MagicMock, token: str):
    """
    Test if the function raises JWTBlackListException when the token is in the blacklist.

    Args:
        token_secret_mock: Mocked environment variable for JWT secret.
        token (str): The JWT.
    """
    expected_dict_with_code_and_detail = token_exception_messages.TOKEN_IN_BLACKLIST
    payload: dict = jwt.decode(token, FAKE_SECRET, algorithms="HS256")

    JWTBlackList.objects.create(
        jti=payload["jti"],
        exp=payload["exp"],
        typ=payload["typ"],
    )
    with pytest.raises(JWTBlackListException) as e:
        check_token(token)

    assert expected_dict_with_code_and_detail == e.value.dict_repr()


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get_path_for_mock}",
    return_value=FAKE_SECRET,
)
def test_success_create_token(
    token_secret_mock: MagicMock, token: str, fake_payload: dict
):
    """
    Test to ensure that a JWT is successfully created and can be decoded to match the original payload.

    Args:
        token_secret_mock (MagicMock): Mocked environment variable for JWT secret.
        token (str): JWT token that has been created for the test.
        fake_payload (dict): Original payload used to create the JWT token.
    """
    payload_result: dict = check_token(token)
    assert fake_payload["jti"] == payload_result["jti"]
    assert fake_payload["exp"] == payload_result["exp"]
    assert fake_payload["uid"] == payload_result["uid"]
    assert fake_payload["typ"] == payload_result["typ"]
