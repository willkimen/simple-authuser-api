"""
This module contains tests for the `authenticate()` method of 
the `JWTAuthentication` class.

The tests cover various scenarios related to JWT authentication, including:
- Empty or malformed authorization headers
- Expired JWTs or JWTs with an invalid secret
- Malformed JWTs or JWTs with invalid algorithms
- JWTs that are blacklisted
- JWTs for nonexistent users
- Successful authentication with a valid JWT

It uses the `pytest` and `unittest.mock` libraries.
"""

import base64
import json
from datetime import timedelta
from unittest.mock import MagicMock, patch

import jwt
import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from user_app.authentication_classes import JWTAuthentication
from user_app.constants import (
    authentication_error_messages,
    response_codes_and_messages,
    token_exception_messages,
)
from user_app.constants.path_for_mock import token_utils_module_path
from user_app.models import BlacklistTokenModel

# ============== Objects and constants ===============
User = get_user_model()
factory = RequestFactory()
jwt_authentication = JWTAuthentication()
INCORRECT_TYP = "refresh"
ID = 1
SECRET = "fake_secret"
JTI_IN_BLACKLIST = "fake_jti_in_blacklist"
os_environ_get = "os.environ.get"


# ================== Fixtures ===================
@pytest.fixture
def user_data() -> dict:
    """Create a generic user data."""
    return {
        "id": ID,
        "first_name": "fake_first_name",
        "last_name": "fake_last_name",
        "email": "fakeemail@email.com",
        "password": "fake!_PASSWORD10",
        "is_active": True,
    }


@pytest.fixture
def payload() -> dict:
    """Create a generic payload."""
    return {
        "uid": ID,
        "typ": "access",
        "jti": "fake_jti",
        "exp": int((timezone.now() + timedelta(days=1)).timestamp()),
    }


@pytest.fixture
def activated_user(user_data: dict) -> User:
    """Create and persisted activated user."""
    return User.objects.create_user(**user_data)


@pytest.fixture
def payload_with_activated_user(activated_user: User, payload: dict) -> dict:
    """Create a payload with activated user."""
    payload["uid"] = activated_user.id
    return payload


@pytest.fixture
def token_request_with_activated_user(payload_with_activated_user: dict) -> Request:
    """
    Fixture to create a Django Request object with a valid JWT for an activated user.

    Returns:
        Request: A Django Request object with an Authorization header
                 containing a valid JWT.
    """
    return Request(
        factory.get(
            "/",
            HTTP_AUTHORIZATION=f"Bearer {jwt.encode(payload_with_activated_user, SECRET)}",
        )
    )


@pytest.fixture
def token_request_with_deactivated_user(user_data: dict, payload: dict) -> Request:
    """
    Fixture to create a Django Request object with a JWT for a deactivated user.

    Returns:
        Request: A Django Request object with an Authorization header containing a JWT.
    """

    user_data["is_active"] = False
    deactivated_user = User.objects.create_user(**user_data)
    payload["uid"] = deactivated_user.id

    return Request(
        factory.get(
            "/",
            HTTP_AUTHORIZATION=f"Bearer {jwt.encode(payload, SECRET)}",
        )
    )


@pytest.fixture
def empty_auth_header_request() -> Request:
    """
    Create a request object with an empty Authorization header.

    Returns:
        Request: A request object with an empty Authorization header.
    """
    return Request(factory.get("/", HTTP_AUTHORIZATION=""))


@pytest.fixture
def incorrect_auth_header_request() -> Request:
    """
    Create a request object with an incorrect Authorization header.

    Returns:
        Request: A request object with an incorrect Authorization header.
    """
    return Request(factory.get("/", HTTP_AUTHORIZATION="Type_Incorret"))


@pytest.fixture
def incorrect_format_auth_header_request() -> list[Request]:
    """
    Create a list of request objects with incorrectly formatted Authorization headers.

    Returns:
        list[Request]: A list of request objects with incorrect Authorization headers.
    """
    return [
        Request(factory.get("/", HTTP_AUTHORIZATION="Bearer")),
        Request(factory.get("/", HTTP_AUTHORIZATION="Bearer jwt_fake extra")),
    ]


@pytest.fixture
def token_request_with_nonexistent_user(payload: dict) -> Request:
    """
    Create a request object with a JWT token for a nonexistent user.

    Returns:
        Request: A request object with a JWT token in the Authorization header.
    """

    token = jwt.encode(payload, SECRET)
    return Request(factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}"))


@pytest.fixture
def expired_token_request(payload_with_activated_user: dict) -> Request:
    """
    Create a request object with an expired JWT token.

    Returns:
        Request: A request object with an expired JWT token
                 in the Authorization header.
    """
    # Create a expired date
    exp_expired = int((timezone.now() - timedelta(seconds=10)).timestamp())
    payload_with_activated_user["exp"] = exp_expired

    token = jwt.encode(payload_with_activated_user, SECRET)

    return Request(factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}"))


@pytest.fixture
def token_request_with_invalid_secret(payload_with_activated_user: dict) -> Request:
    """
    Create a request object with a JWT token signed with an incorrect secret.

    Returns:
        Request: A request object with a JWT token signed with an
                 incorrect secret in the Authorization header.
    """
    token = jwt.encode(payload_with_activated_user, "invalid_secret")
    return Request(factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}"))


@pytest.fixture
def malformed_token_request() -> Request:
    """
    Create a request object with a malformed JWT token.

    Returns:
        Request: A request object with a malformed JWT token
                 in the Authorization header.
    """

    return Request(factory.get("/", HTTP_AUTHORIZATION="Bearer malformed.token.string"))


@pytest.fixture
def token_request_with_invalid_algorithm(payload_with_activated_user: dict) -> Request:
    """
    Create a request object with a JWT token that has an invalid algorithm.

    Returns:
        Request: A request object with a JWT token that
                 specifies an invalid algorithm in the header.
    """

    # Encode the payload into a JWT token with the correct secret
    token = jwt.encode(payload_with_activated_user, SECRET)

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
    token_with_invalid_algorithm = f"{modified_header}.{payload}.{signature}"

    # Create and return a request object with the
    # JWT token that has an invalid algorithm
    return Request(
        factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token_with_invalid_algorithm}")
    )


@pytest.fixture
def request_with_blacklisted_token(payload_with_activated_user: User) -> Request:
    """
    Create a request object with a JWT token that is blacklisted.

    Returns:
        Request: A request object with a JWT token that has a JTI in the blacklist.
    """

    payload_with_activated_user["jti"] = JTI_IN_BLACKLIST

    token = jwt.encode(payload_with_activated_user, SECRET)

    BlacklistTokenModel.objects.create(
        user_id=payload_with_activated_user["uid"],
        jti=payload_with_activated_user["jti"],
        exp=payload_with_activated_user["exp"],
        typ=payload_with_activated_user["typ"],
    )

    return Request(factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}"))


@pytest.fixture
def request_with_incorrect_type_token(payload_with_activated_user: dict) -> Request:
    """
    Create a request object with a JWT token with incorrect type token.
    """
    payload_with_activated_user["typ"] = INCORRECT_TYP

    token = jwt.encode(payload_with_activated_user, SECRET)

    return Request(factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}"))


# ================ Tests =======================
@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
def test_authentication_fails_when_token_type_is_incorrect(
    mock_token_secret: MagicMock,
    request_with_incorrect_type_token: Request,
):
    """
    Test that authentication fails when the JWT token type ("typ") is incorrect.

    Args:
        mock_token_secret (MagicMock): Mock object for retrieving the JWT
                                       secret from environment variables.
        request_with_incorrect_type_token (Request): The request fixture containing a
                                                     JWT token with an incorrect type.
    """
    expected_error_message = response_codes_and_messages.IS_NOT_ACCESS_TOKEN["detail"]
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(request_with_incorrect_type_token)

    assert expected_error_message == str(e.value)


def test_authentication_fails_when_empty_auth_header(
    empty_auth_header_request: Request,
):
    """
    Test that authentication fails when the Authorization header is empty.

    Args:
        empty_auth_header_request (Request): A request object with an empty
                                             Authorization header.
    """
    expected_error_message = authentication_error_messages.AUTHORIZATION_HEADER_MISSING
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(empty_auth_header_request)

    assert expected_error_message == str(e.value)


def test_authentication_fails_when_incorrect_type_auth_header(
    incorrect_auth_header_request: Request,
):
    """
    Test that authentication fails when the Authorization header has an incorrect type.

    Args:
        incorrect_auth_header_request (Request): A request object with an
                                                 incorrect Authorization header type.
    """
    expected_error_message = (
        authentication_error_messages.AUTHORIZATION_HEADER_WITHOUT_BEARER
    )
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(incorrect_auth_header_request)

    assert expected_error_message == str(e.value)


def test_authentication_fails_when_incorrect_format_auth_header(
    incorrect_format_auth_header_request: list[Request],
):
    """
    Test that authentication fails when the Authorization header
    is in an incorrect format.

    Args:
        incorrect_format_auth_header_request (list[Request]): A list of request objects
                                                              with incorrectly formatted
                                                              Authorization headers.
    """
    expected_error_message = (
        authentication_error_messages.INVALID_AUTHORIZATION_HEADER_FORMAT
    )

    for request in incorrect_format_auth_header_request:
        with pytest.raises(AuthenticationFailed) as e:
            jwt_authentication.authenticate(request)

        assert expected_error_message == str(e.value)


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
def test_authentication_fails_when_expired_token(
    mock_token_secret: MagicMock,
    expired_token_request: Request,
):
    """
    Test that authentication fails when the JWT is expired.

    Args:
        mock_token_secret (MagicMock): Mocked environment variable for JWT secret.
        expired_token_request (Request): Request object with an expired
                                         JWT in the Authorization header.
    """
    expected_error_message = token_exception_messages.EXPIRED_SIGNATURE["detail"]
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(expired_token_request)

    assert expected_error_message == str(e.value)


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
def test_authentication_fails_when_invalid_secret_token(
    mock_token_secret: MagicMock,
    token_request_with_invalid_secret: Request,
):
    """
    Test that authentication fails when the JWT has an invalid secret.

    Args:
        mock_token_secret (MagicMock): Mocked environment variable for JWT secret.
        token_request_with_invalid_secret (Request): Request object with a JWT
                                                     encoded using an incorrect secret.
    """
    expected_error_message = token_exception_messages.INVALID_SIGNATURE["detail"]
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(token_request_with_invalid_secret)

    assert expected_error_message == str(e.value)


@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
def test_authentication_fails_when_malformed_token(
    mock_token_secret: MagicMock,
    malformed_token_request: Request,
):
    """
    Test that authentication fails when the JWT is malformed.

    Args:
        mock_token_secret (MagicMock): Mocked environment variable for JWT secret.
        malformed_token_request (Request): Request object with a malformed JWT.
    """
    expected_error_message = token_exception_messages.DECODE_ERROR["detail"]
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(malformed_token_request)

    assert expected_error_message == str(e.value)


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
def test_authentication_fails_when_invalid_algorithm_token(
    mock_token_secret: MagicMock,
    token_request_with_invalid_algorithm: Request,
):
    """
    Test to ensure that authentication fails when the JWT uses an invalid algorithm.

    Args:
        mock_token_secret: Mocked environment variable for JWT secret.
        token_request_with_invalid_algorithm (Request): Request object containing a
                                                        JWT with an invalid algorithm.
    """
    expected_error_message = token_exception_messages.INVALID_ALGORITHM["detail"]
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(token_request_with_invalid_algorithm)

    assert expected_error_message == str(e.value)


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
def test_authentication_fails_when_blacklisted_token(
    mock_token_secret: MagicMock,
    request_with_blacklisted_token: Request,
):
    """
    Test that authentication fails when the JWT is blacklisted.

    Args:
        mock_token_secret (MagicMock): Mocked environment variable for JWT secret.
        request_with_blacklisted_token (Request): Request object with a blacklisted JWT.
    """

    expected_error_message = token_exception_messages.TOKEN_IN_BLACKLIST["detail"]
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(request_with_blacklisted_token)

    assert expected_error_message == str(e.value)


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
def test_authentication_fails_when_nonexistent_user(
    mock_token_secret: MagicMock,
    token_request_with_nonexistent_user: Request,
):
    """
    Test that authentication fails when the JWT is for a nonexistent user.

    Args:
        mock_token_secret (MagicMock): Mocked environment variable for JWT secret.
        token_request_with_nonexistent_user (Request): Request object with a
                                                       JWT for a nonexistent user.
    """
    expected_error_message = response_codes_and_messages.USER_NOT_FOUND["detail"]
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(token_request_with_nonexistent_user)

    assert expected_error_message == str(e.value)


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
def test_authentication_success(
    mock_token_secret: MagicMock,
    token_request_with_activated_user: Request,
    activated_user: User,
    payload_with_activated_user: dict,
):
    """
    Test that the authentication succeeds for an activated user.

    Args:
        mock_token_secret (MagicMock): Mock for the environment variable
                                       holding the JWT secret.
        token_request_with_activated_user (Request): The request containing a
                                                     JWT for an activated user.
        activated_user (User): The activated user instance.
        payload_with_activated_user (dict): The expected payload of the
                                            JWT for the activated user.

    Asserts:
        The authenticated user's details match the expected user, and the JWT
        payload is correct.
    """
    user_actual, payload_actual = jwt_authentication.authenticate(
        token_request_with_activated_user
    )

    assert activated_user.id == user_actual.id
    assert activated_user.first_name == user_actual.first_name
    assert activated_user.last_name == user_actual.last_name
    assert activated_user.email == user_actual.email
    assert activated_user.password == user_actual.password
    assert activated_user.is_active == user_actual.is_active
    assert payload_with_activated_user == payload_actual


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get}",
    return_value=SECRET,
)
def test_authentication_fails_when_user_with_account_deactivated(
    mock_token_secret: MagicMock,
    token_request_with_deactivated_user: Request,
):
    """
    Test that authentication fails when the user account is deactivated.

    Args:
        mock_token_secret (MagicMock): Mock for the environment variable
                                       holding the JWT secret.
        token_request_with_deactivated_user (Request): The request containing a
                                                        JWT for a deactivated user.

    Asserts:
        The authentication fails with the appropriate error message
        indicating the user's account is not activated.
    """
    expected_error_message = response_codes_and_messages.USER_ACCOUNT_NOT_ACTIVATED["detail"]
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(token_request_with_deactivated_user)

    assert expected_error_message == str(e.value)
