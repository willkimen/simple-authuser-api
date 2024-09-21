"""
This module contains tests for the `authenticate()` method of the `JWTAuthentication` class.

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
    response_code_messages,
    token_exception_messages,
)
from user_app.constants.path_for_mock import token_utils_module_path
from user_app.models import BlacklistTokenModel

# ============== Objects and constants ===============
User = get_user_model()
factory = RequestFactory()
jwt_authentication = JWTAuthentication()
INCORRECT_TYP = "refresh"
FAKE_SECRET = "fake_secret"
FAKE_JTI_IN_BLACKLIST = "fake_jti_in_blacklist"
FAKE_UID = 10
FAKE_TYP = "access"
FAKE_JTI = "fake_jti"
FAKE_EXP = int((timezone.now() + timedelta(days=1)).timestamp())
FAKE_FIRST_NAME = "fake_first_name"
FAKE_LAST_NAME = "fake_last_name"
FAKE_EMAIL = "fake_email@email.com"
FAKE_PASSWORD = "fale_password"
os_environ_get_path_for_mock = "os.environ.get"


# ================== Fixtures ===================
@pytest.fixture
def user_activated() -> User:
    """Create and persisted activated user."""
    return User.objects.create_user(
        id=FAKE_UID,
        first_name=FAKE_FIRST_NAME,
        last_name=FAKE_LAST_NAME,
        email=FAKE_EMAIL,
        password=FAKE_PASSWORD,
        is_active=True,
    )


@pytest.fixture
def payload_with_user_activated(user_activated) -> dict:
    """Create a payload with activated user."""
    return {
        "uid": user_activated.id,
        "typ": FAKE_TYP,
        "jti": FAKE_JTI,
        "exp": FAKE_EXP,
    }


@pytest.fixture
def token_request_with_user_activated(payload_with_user_activated) -> Request:
    """
    Fixture to create a Django Request object with a valid JWT for an activated user.

    Returns:
        Request: A Django Request object with an Authorization header
                 containing a valid JWT.
    """
    return Request(
        factory.get(
            "/",
            HTTP_AUTHORIZATION=f"Bearer {jwt.encode(payload_with_user_activated, FAKE_SECRET)}",
        )
    )


@pytest.fixture
def token_request_with_user_desactivated() -> Request:
    """
    Fixture to create a Django Request object with a JWT for a deactivated user.

    Returns:
        Request: A Django Request object with an Authorization header containing a JWT.
    """

    user_desactivated = User.objects.create_user(
        id=FAKE_UID,
        first_name=FAKE_FIRST_NAME,
        last_name=FAKE_LAST_NAME,
        email=FAKE_EMAIL,
        password=FAKE_PASSWORD,
        is_active=False,
    )

    payload = {
        "uid": user_desactivated.id,
        "typ": FAKE_TYP,
        "jti": FAKE_JTI,
        "exp": FAKE_EXP,
    }

    return Request(
        factory.get(
            "/",
            HTTP_AUTHORIZATION=f"Bearer {jwt.encode(payload, FAKE_SECRET)}",
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
def token_request_with_nonexistent_user() -> Request:
    """
    Create a request object with a JWT token for a nonexistent user.

    Returns:
        Request: A request object with a JWT token in the Authorization header.
    """

    payload = {
        "uid": FAKE_UID,
        "typ": FAKE_TYP,
        "jti": FAKE_JTI,
        "exp": FAKE_EXP,
    }

    token = jwt.encode(payload, FAKE_SECRET)
    return Request(factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}"))


@pytest.fixture
def expired_token_request() -> Request:
    """
    Create a request object with an expired JWT token.

    Returns:
        Request: A request object with an expired JWT token
                 in the Authorization header.
    """
    user = User.objects.create_user(
        id=FAKE_UID,
        first_name=FAKE_FIRST_NAME,
        last_name=FAKE_LAST_NAME,
        email=FAKE_EMAIL,
        password=FAKE_PASSWORD,
        is_active=True,
    )

    # Create a expired date
    exp_expired = int((timezone.now() - timedelta(seconds=10)).timestamp())

    payload = {
        "uid": user.id,
        "typ": FAKE_TYP,
        "jti": FAKE_JTI,
        "exp": exp_expired,
    }

    token = jwt.encode(payload, FAKE_SECRET)

    return Request(factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}"))


@pytest.fixture
def token_request_with_invalid_secret() -> Request:
    """
    Create a request object with a JWT token signed with an incorrect secret.

    Returns:
        Request: A request object with a JWT token signed with an
                 incorrect secret in the Authorization header.
    """
    user = User.objects.create_user(
        id=FAKE_UID,
        first_name=FAKE_FIRST_NAME,
        last_name=FAKE_LAST_NAME,
        email=FAKE_EMAIL,
        password=FAKE_PASSWORD,
        is_active=True,
    )

    payload = {
        "uid": user.id,
        "typ": FAKE_TYP,
        "jti": FAKE_JTI,
        "exp": FAKE_EXP,
    }

    token = jwt.encode(payload, "invalid_secret")

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
def token_request_with_invalid_algorithm() -> Request:
    """
    Create a request object with a JWT token that has an invalid algorithm.

    Returns:
        Request: A request object with a JWT token that
                 specifies an invalid algorithm in the header.
    """

    user = User.objects.create_user(
        id=FAKE_UID,
        first_name=FAKE_FIRST_NAME,
        last_name=FAKE_LAST_NAME,
        email=FAKE_EMAIL,
        password=FAKE_PASSWORD,
        is_active=True,
    )

    payload = {
        "uid": user.id,
        "typ": FAKE_TYP,
        "jti": FAKE_JTI,
        "exp": FAKE_EXP,
    }

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
    token_with_invalid_algorithm = f"{modified_header}.{payload}.{signature}"

    # Create and return a request object with the JWT token that has an invalid algorithm
    return Request(
        factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token_with_invalid_algorithm}")
    )


@pytest.fixture
def request_with_blacklisted_token() -> Request:
    """
    Create a request object with a JWT token that is blacklisted.

    Returns:
        Request: A request object with a JWT token that has a JTI in the blacklist.
    """
    user = User.objects.create_user(
        id=FAKE_UID,
        first_name=FAKE_FIRST_NAME,
        last_name=FAKE_LAST_NAME,
        email=FAKE_EMAIL,
        password=FAKE_PASSWORD,
        is_active=True,
    )

    payload = {
        "uid": user.id,
        "typ": FAKE_TYP,
        "jti": FAKE_JTI_IN_BLACKLIST,
        "exp": FAKE_EXP,
    }

    token = jwt.encode(payload, FAKE_SECRET)

    BlacklistTokenModel.objects.create(
        user_id=FAKE_UID,
        jti=payload["jti"],
        exp=payload["exp"],
        typ=payload["typ"],
    )

    return Request(factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}"))


@pytest.fixture
def request_with_incorrect_type_token() -> Request:
    """
    Create a request object with a JWT token with incorrect type token.
    """
    user = User.objects.create_user(
        id=FAKE_UID,
        first_name=FAKE_FIRST_NAME,
        last_name=FAKE_LAST_NAME,
        email=FAKE_EMAIL,
        password=FAKE_PASSWORD,
        is_active=True,
    )

    payload = {
        "uid": user.id,
        "typ": INCORRECT_TYP,
        "jti": FAKE_JTI,
        "exp": FAKE_EXP,
    }

    token = jwt.encode(payload, FAKE_SECRET)

    return Request(factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}"))


# ================ Tests =======================
@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get_path_for_mock}",
    return_value=FAKE_SECRET,
)
def test_authentication_fails_when_token_type_is_incorrect(
    mock_token_secret: MagicMock,
    request_with_incorrect_type_token: Request,
):
    """
    Test that authentication fails when the JWT token type ("typ") is incorrect.

    Args:
        mock_token_secret (MagicMock): Mock object for retrieving the JWT secret from environment variables.
        request_with_incorrect_type_token (Request): The request fixture containing a JWT token with an incorrect type.
    """
    expected_error_message = response_code_messages.IS_NOT_ACCESS_TOKEN["detail"]
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(request_with_incorrect_type_token)

    assert expected_error_message == str(e.value)


@pytest.mark.django_db
def test_authentication_fails_when_empty_auth_header(
    empty_auth_header_request: Request,
):
    """
    Test that authentication fails when the Authorization header is empty.

    Args:
        empty_auth_header_request (Request): A request object with an empty Authorization header.
    """
    expected_error_message = authentication_error_messages.AUTHORIZATION_HEADER_MISSING
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(empty_auth_header_request)

    assert expected_error_message == str(e.value)


@pytest.mark.django_db
def test_authentication_fails_when_incorrect_type_auth_header(
    incorrect_auth_header_request: Request,
):
    """
    Test that authentication fails when the Authorization header has an incorrect type.

    Args:
        incorrect_auth_header_request (Request): A request object with an incorrect Authorization header type.
    """
    expected_error_message = (
        authentication_error_messages.AUTHORIZATION_HEADER_WITHOUT_BEARER
    )
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(incorrect_auth_header_request)

    assert expected_error_message == str(e.value)


@pytest.mark.django_db
def test_authentication_fails_when_incorrect_format_auth_header(
    incorrect_format_auth_header_request: list[Request],
):
    """
    Test that authentication fails when the Authorization header is in an incorrect format.

    Args:
        incorrect_format_auth_header_request (list[Request]): A list of request objects with incorrectly formatted Authorization headers.
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
    f"{token_utils_module_path}.{os_environ_get_path_for_mock}",
    return_value=FAKE_SECRET,
)
def test_authentication_fails_when_expired_token(
    mock_token_secret: MagicMock,
    expired_token_request: Request,
):
    """
    Test that authentication fails when the JWT is expired.

    Args:
        mock_token_secret (MagicMock): Mocked environment variable for JWT secret.
        expired_token_request (Request): Request object with an expired JWT in the Authorization header.
    """
    expected_error_message = token_exception_messages.EXPIRED_SIGNATURE["detail"]
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(expired_token_request)

    assert expected_error_message == str(e.value)


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get_path_for_mock}",
    return_value=FAKE_SECRET,
)
def test_authentication_fails_when_invalid_secret_token(
    mock_token_secret: MagicMock,
    token_request_with_invalid_secret: Request,
):
    """
    Test that authentication fails when the JWT has an invalid secret.

    Args:
        mock_token_secret (MagicMock): Mocked environment variable for JWT secret.
        token_request_with_invalid_secret (Request): Request object with a JWT encoded using an incorrect secret.
    """
    expected_error_message = token_exception_messages.INVALID_SIGNATURE["detail"]
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(token_request_with_invalid_secret)

    assert expected_error_message == str(e.value)


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get_path_for_mock}",
    return_value=FAKE_SECRET,
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
    f"{token_utils_module_path}.{os_environ_get_path_for_mock}",
    return_value=FAKE_SECRET,
)
def test_authentication_fails_when_invalid_algorithm_token(
    mock_token_secret: MagicMock,
    token_request_with_invalid_algorithm: Request,
):
    """
    Test to ensure that authentication fails when the JWT uses an invalid algorithm.

    Args:
        mock_token_secret: Mocked environment variable for JWT secret.
        token_request_with_invalid_algorithm (Request): Request object containing a JWT with an invalid algorithm.
    """
    expected_error_message = token_exception_messages.INVALID_ALGORITHM["detail"]
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(token_request_with_invalid_algorithm)

    assert expected_error_message == str(e.value)


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get_path_for_mock}",
    return_value=FAKE_SECRET,
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
    f"{token_utils_module_path}.{os_environ_get_path_for_mock}",
    return_value=FAKE_SECRET,
)
def test_authentication_fails_when_nonexistent_user(
    mock_token_secret: MagicMock,
    token_request_with_nonexistent_user: Request,
):
    """
    Test that authentication fails when the JWT is for a nonexistent user.

    Args:
        mock_token_secret (MagicMock): Mocked environment variable for JWT secret.
        token_request_with_nonexistent_user (Request): Request object with a JWT for a nonexistent user.
    """
    expected_error_message = response_code_messages.USER_NOT_FOUND["detail"]
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(token_request_with_nonexistent_user)

    assert expected_error_message == str(e.value)


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get_path_for_mock}",
    return_value=FAKE_SECRET,
)
def test_authentication_success(
    mock_token_secret: MagicMock,
    token_request_with_user_activated: Request,
    user_activated: User,
    payload_with_user_activated: dict,
):
    """
    Test that the authentication succeeds for an activated user.

    Args:
        mock_token_secret (MagicMock): Mock for the environment variable holding the JWT secret.
        token_request_with_user_activated (Request): The request containing a JWT for an activated user.
        user_activated (User): The activated user instance.
        payload_with_user_activated (dict): The expected payload of the JWT for the activated user.

    Asserts:
        The authenticated user's details match the expected user, and the JWT payload is correct.
    """
    user_actual, payload_actual = jwt_authentication.authenticate(
        token_request_with_user_activated
    )

    assert user_activated.id == user_actual.id
    assert user_activated.first_name == user_actual.first_name
    assert user_activated.last_name == user_actual.last_name
    assert user_activated.email == user_actual.email
    assert user_activated.password == user_actual.password
    assert user_activated.is_active == user_actual.is_active
    assert payload_with_user_activated == payload_actual


@pytest.mark.django_db
@patch(
    f"{token_utils_module_path}.{os_environ_get_path_for_mock}",
    return_value=FAKE_SECRET,
)
def test_authentication_fails_when_user_with_account_desactivated(
    mock_token_secret: MagicMock,
    token_request_with_user_desactivated: Request,
):
    """
    Test that authentication fails when the user account is deactivated.

    Args:
        mock_token_secret (MagicMock): Mock for the environment variable holding the JWT secret.
        token_request_with_user_desactivated (Request): The request containing a JWT for a deactivated user.

    Asserts:
        The authentication fails with the appropriate error message indicating the user's account is not activated.
    """
    expected_error_message = response_code_messages.USER_ACCOUNT_NOT_ACTIVATED["detail"]
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(token_request_with_user_desactivated)

    assert expected_error_message == str(e.value)
