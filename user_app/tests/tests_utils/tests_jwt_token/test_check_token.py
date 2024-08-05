import base64
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
import pytest

from user_app.exceptions import JWTBlackListException
from user_app.models import JWTBlackList
from user_app.utils.jwt_token import check_token

JWT_SECRET_FOR_TESTS = "jwt_secret"


@pytest.fixture
def token_expired() -> str:
    """
    Fixture that creates an expired JWT for testing purposes.

    Returns:
        str: The expired JWT.
    """
    payload = {
        "uid": 10,
        "typ": "access",
        "jti": "test_jti",
        "exp": int((datetime.now() - timedelta(seconds=10)).timestamp()),
    }

    return jwt.encode(payload, JWT_SECRET_FOR_TESTS)


@pytest.fixture
def token_with_incorret_secret() -> str:
    """
    Fixture that creates a JWT with an incorrect secret for testing purposes.

    Returns:
        str: The JWT with an incorrect secret.
    """
    payload = {
        "uid": 10,
        "typ": "access",
        "jti": "test_jti",
        "exp": int((datetime.now() + timedelta(days=1)).timestamp()),
    }

    return jwt.encode(payload, "incorrect_secret")


@pytest.fixture
def token_malformed() -> str:
    """
    Fixture that creates a malformed JWT for testing purposes.

    Returns:
        str: The malformed JWT.
    """
    return "malformed.token.string"


@pytest.fixture
def token() -> str:
    """
    Fixture that creates a valid JWT for testing purposes.

    Returns:
        str: The valid JWT.
    """
    payload = {
        "uid": 10,
        "typ": "access",
        "jti": "test_jti",
        "exp": int((datetime.now() + timedelta(days=1)).timestamp()),
    }

    return jwt.encode(payload, JWT_SECRET_FOR_TESTS)


@pytest.fixture
def token_and_payload() -> dict:
    """
    Fixture that creates a valid JWT and its payload for testing purposes.

    Returns:
        dict: A dictionary containing the JWT and its payload.
    """
    payload = {
        "uid": 10,
        "typ": "access",
        "jti": "test_jti",
        "exp": int((datetime.now() + timedelta(days=1)).timestamp()),
    }
    return {
        "token": jwt.encode(payload, JWT_SECRET_FOR_TESTS),
        "payload": payload,
    }


@pytest.fixture
def token_with_invalid_algorithm() -> str:
    """
    Fixture that creates a JWT with an invalid algorithm for testing purposes.

    Returns:
        str: The JWT with an invalid algorithm.
    """
    payload = {
        "uid": 10,
        "typ": "access",
        "jti": "test_jti",
        "exp": int((datetime.now() + timedelta(days=1)).timestamp()),
    }
    token = jwt.encode(payload, JWT_SECRET_FOR_TESTS)
    header, payload, signature = token.split(".")
    header_data = json.loads(base64.urlsafe_b64decode(header + "==").decode("utf-8"))
    header_data["alg"] = "RS256"  # Invalid algorithm
    modified_header = (
        base64.urlsafe_b64encode(json.dumps(header_data).encode("utf-8"))
        .decode("utf-8")
        .rstrip("=")
    )
    return f"{modified_header}.{payload}.{signature}"


@patch("user_app.utils.jwt_token.os.environ.get", return_value=JWT_SECRET_FOR_TESTS)
def test_token_expired(jwt_secret_mock, token_expired):
    """
    Test if the function raises ExpiredSignatureError when the token is expired.

    Args:
        jwt_secret_mock: Mocked environment variable for JWT secret.
        token_expired (str): The expired JWT.
    """
    with pytest.raises(jwt.exceptions.ExpiredSignatureError):
        check_token(token_expired)


@patch("user_app.utils.jwt_token.os.environ.get", return_value=JWT_SECRET_FOR_TESTS)
def test_invalid_signature(jwt_secret_mock, token_with_incorret_secret):
    """
    Test if the function raises InvalidSignatureError when the token has an invalid signature.

    Args:
        jwt_secret_mock: Mocked environment variable for JWT secret.
        token_with_incorret_secret (str): The JWT with an incorrect secret.
    """
    with pytest.raises(jwt.exceptions.InvalidSignatureError):
        check_token(token_with_incorret_secret)


@patch("user_app.utils.jwt_token.os.environ.get", return_value=JWT_SECRET_FOR_TESTS)
def test_decode_error(jwt_secret_mock, token_malformed):
    """
    Test if the function raises DecodeError when the token is malformed.

    Args:
        jwt_secret_mock: Mocked environment variable for JWT secret.
        token_malformed (str): The malformed JWT.
    """
    with pytest.raises(jwt.exceptions.DecodeError):
        check_token(token_malformed)


@patch("user_app.utils.jwt_token.os.environ.get", return_value=JWT_SECRET_FOR_TESTS)
def test_invalid_algorithm(jwt_secret_mock, token_with_invalid_algorithm):
    """
    Test if the function raises InvalidAlgorithmError when the token has an invalid algorithm.

    Args:
        jwt_secret_mock: Mocked environment variable for JWT secret.
        token_with_invalid_algorithm (str): The JWT with an invalid algorithm.
    """
    with pytest.raises(jwt.exceptions.InvalidAlgorithmError):
        check_token(token_with_invalid_algorithm)


@pytest.mark.django_db
@patch("user_app.utils.jwt_token.os.environ.get", return_value=JWT_SECRET_FOR_TESTS)
def test_jwt_in_black_list(jwt_secret_mock, token):
    """
    Test if the function raises JWTBlackListException when the token is in the blacklist.

    Args:
        jwt_secret_mock: Mocked environment variable for JWT secret.
        token (str): The JWT.
    """
    payload = jwt.decode(token, JWT_SECRET_FOR_TESTS, algorithms="HS256")

    JWTBlackList.objects.create(
        jti=payload["jti"],
        exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        typ=payload["typ"],
    )
    with pytest.raises(JWTBlackListException):
        check_token(token)


@pytest.mark.django_db
@patch("user_app.utils.jwt_token.os.environ.get", return_value=JWT_SECRET_FOR_TESTS)
def test_create_token_is_success(jwt_secret_mock, token_and_payload: dict):
    """
    Test if the function successfully decodes a valid JWT.

    Args:
        jwt_secret_mock: Mocked environment variable for JWT secret.
        token_and_payload (dict): A dictionary containing the JWT and its payload.
    """
    token, payload_expected = token_and_payload.values()
    payload: dict = check_token(token)
    assert payload_expected["jti"] == payload["jti"]
    assert payload_expected["exp"] == payload["exp"]
    assert payload_expected["uid"] == payload["uid"]
    assert payload_expected["typ"] == payload["typ"]
