"""
This module tests the check_token() function, which takes a JWT as an argument 
and returns the payload. 
It tests all possible exceptions raised as well as the success scenario.
"""

import base64
import json
from datetime import timedelta
from unittest.mock import patch

import jwt
import pytest
from django.utils import timezone
from user_app.authentication.token_exceptions import (
    BlacklistTokenException,
    DecodeException,
    ExpiredSignatureException,
    InvalidAlgorithmException,
    InvalidSignatureException,
)
from user_app.authentication.token_service import check_token
from user_app.constants import authentication
from user_app.models import BlacklistTokenModel
from user_app.tests.constants import (
    FAKE_SECRET,
    TOKEN_SECRET_SETTING_TO_PATCH,
    TOKEN_UTILS_MODULE_PATH,
)

# ========== Objects and constants ============
INVALID_SECRET = "invalid_secret"
MALFORMED_TOKEN = "malformed.token.string"


# ============== Fixture ==================
@pytest.fixture
def token_expired(payload: dict) -> str:
    """
    Fixture that creates an expired JWT for testing purposes.

    Returns:
        str: The expired JWT.
    """
    payload["exp"] = int((timezone.now() - timedelta(seconds=60)).timestamp())

    return jwt.encode(payload, FAKE_SECRET)


@pytest.fixture
def token_with_invalid_secret(payload: dict) -> str:
    """
    Fixture that creates a JWT with an invalid secret for testing purposes.

    Returns:
        str: The JWT with an invalid secret.
    """
    return jwt.encode(payload, INVALID_SECRET)


@pytest.fixture
def token_malformed() -> str:
    """
    Fixture that creates a malformed JWT for testing purposes.

    Returns:
        str: The malformed JWT.
    """
    return MALFORMED_TOKEN


@pytest.fixture
def token(payload: dict) -> str:
    """
    Fixture that creates a valid JWT for testing purposes.

    Returns:
        str: The valid JWT.
    """
    return jwt.encode(payload, FAKE_SECRET)


@pytest.fixture
def token_with_invalid_algorithm(payload: dict) -> str:
    """
    Fixture that creates a JWT with an invalid algorithm for testing purposes.

    Returns:
        str: The JWT with an invalid algorithm.
    """
    # Encode the payload into a JWT token with the correct secret
    token = jwt.encode(payload, FAKE_SECRET)

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
@pytest.mark.django_db
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_expired_token(token_expired: str):
    """
    Test if the function raises ExpiredSignatureError when the token is expired.

    Args:
        token_expired (str): The expired JWT.
    """
    expected_dict_with_code_and_detail = authentication.EXPIRED_SIGNATURE
    with pytest.raises(ExpiredSignatureException) as e:
        check_token(token_expired)

    assert expected_dict_with_code_and_detail == e.value.dict_repr()


@pytest.mark.django_db
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_invalid_signature(token_with_invalid_secret: str):
    """
    Test if the function raises InvalidSignatureError when the token has
    an invalid signature.

    Args:
        token_with_invalid_secret (str): The JWT with an incorrect secret.
    """
    expected_dict_with_code_and_detail = authentication.INVALID_SIGNATURE
    with pytest.raises(InvalidSignatureException) as e:
        check_token(token_with_invalid_secret)

    assert expected_dict_with_code_and_detail == e.value.dict_repr()


@pytest.mark.django_db
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_decode_error(token_malformed: str):
    """
    Test if the function raises DecodeError when the token is malformed.

    Args:
        token_malformed (str): The malformed JWT.
    """
    expected_dict_with_code_and_detail = authentication.DECODE_ERROR
    with pytest.raises(DecodeException) as e:
        check_token(token_malformed)

    assert expected_dict_with_code_and_detail == e.value.dict_repr()


@pytest.mark.django_db
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_invalid_algorithm(token_with_invalid_algorithm: str):
    """
    Test if the function raises InvalidAlgorithmError when the token has
    an invalid algorithm.

    Args:
        token_with_invalid_algorithm (str): The JWT with an invalid algorithm.
    """
    expected_dict_with_code_and_detail = authentication.INVALID_ALGORITHM
    with pytest.raises(InvalidAlgorithmException) as e:
        check_token(token_with_invalid_algorithm)

    assert expected_dict_with_code_and_detail == e.value.dict_repr()


@pytest.mark.django_db
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_token_in_black_list(token: str):
    """
    Test if the function raises BlacklistTokenException when the token is
    in the blacklist.

    Args:
        token (str): The JWT.
    """
    expected_dict_with_code_and_detail = authentication.TOKEN_IN_BLACKLIST
    payload: dict = jwt.decode(token, FAKE_SECRET, algorithms="HS256")

    BlacklistTokenModel.objects.create(
        account_id=payload["uid"],
        jti=payload["jti"],
        exp=payload["exp"],
        typ=payload["typ"],
    )
    with pytest.raises(BlacklistTokenException) as e:
        check_token(token)

    assert expected_dict_with_code_and_detail == e.value.dict_repr()


@pytest.mark.django_db
@patch(f"{TOKEN_UTILS_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_success_create_token(token: str, payload: dict):
    """
    Test to ensure that a JWT is successfully created and can be decoded to match
    the original payload.

    Args:
        token (str): JWT token that has been created for the test.
        payload (dict): Original payload used to create the JWT token.
    """
    payload_result: dict = check_token(token)
    assert payload["jti"] == payload_result["jti"]
    assert payload["exp"] == payload_result["exp"]
    assert payload["uid"] == payload_result["uid"]
    assert payload["typ"] == payload_result["typ"]
