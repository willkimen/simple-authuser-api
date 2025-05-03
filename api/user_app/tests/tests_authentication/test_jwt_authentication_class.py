"""
This module contains tests for the `authenticate()` method of 
the `JWTAuthentication` class.

The tests cover various scenarios related to JWT authentication, including:
- Empty or malformed authorization headers
- Expired JWTs or JWTs with an invalid secret
- Malformed JWTs or JWTs with invalid algorithms
- JWTs that are blacklisted
- JWTs for nonexistent accounts
- Successful authentication with a valid JWT

It uses the `pytest` and `unittest.mock` libraries.
"""

import base64
import json
from datetime import timedelta
from unittest.mock import patch

import jwt
import pytest
from django.test import RequestFactory
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from user_app.authentication.authentication_classes import JWTAuthentication
from user_app.constants import authentication, http_response
from user_app.models import BlacklistTokenModel
from user_app.tests.constants import (
    FAKE_SECRET,
    TOKEN_SECRET_SETTING_TO_PATCH,
    TOKEN_SERVICE_MODULE_PATH,
    Account,
)

# ============== Objects and constants ===============
factory = RequestFactory()
jwt_authentication = JWTAuthentication()
INCORRECT_TYP = "refresh"
ID = 1
JTI_IN_BLACKLIST = "fake_jti_in_blacklist"


# ================== Fixtures ===================
@pytest.fixture
def account_data() -> dict:
    """Create a generic account data."""
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
def activated_account(account_data: dict):
    """Create and persisted activated account."""
    return Account.objects.create_user(**account_data)


@pytest.fixture
def payload_with_activated_account(activated_account, payload: dict) -> dict:
    """Create a payload with activated account."""
    payload["uid"] = activated_account.id
    return payload


@pytest.fixture
def token_request_with_activated_account(
    payload_with_activated_account: dict,
) -> Request:
    """
    Fixture to create a Django Request object with a valid JWT for an activated account.

    Returns:
        Request: A Django Request object with an Authorization header
                 containing a valid JWT.
    """
    return Request(
        factory.get(
            "/",
            HTTP_AUTHORIZATION=f"Bearer {jwt.encode(payload_with_activated_account, FAKE_SECRET)}",
        )
    )


@pytest.fixture
def token_request_with_deactivated_account(
    account_data: dict, payload: dict
) -> Request:
    """
    Fixture to create a Django Request object with a JWT for a deactivated account.

    Returns:
        Request: A Django Request object with an Authorization header containing a JWT.
    """

    account_data["is_active"] = False
    deactivated_account = Account.objects.create_user(**account_data)
    payload["uid"] = deactivated_account.id

    return Request(
        factory.get(
            "/", HTTP_AUTHORIZATION=f"Bearer {jwt.encode(payload, FAKE_SECRET)}"
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
def token_request_with_nonexistent_account(payload: dict) -> Request:
    """
    Create a request object with a JWT token for a nonexistent account.

    Returns:
        Request: A request object with a JWT token in the Authorization header.
    """

    token = jwt.encode(payload, FAKE_SECRET)
    return Request(factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}"))


@pytest.fixture
def expired_token_request(payload_with_activated_account: dict) -> Request:
    """
    Create a request object with an expired JWT token.

    Returns:
        Request: A request object with an expired JWT token
                 in the Authorization header.
    """
    # Create a expired date
    exp_expired = int((timezone.now() - timedelta(seconds=10)).timestamp())
    payload_with_activated_account["exp"] = exp_expired

    token = jwt.encode(payload_with_activated_account, FAKE_SECRET)

    return Request(factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}"))


@pytest.fixture
def token_request_with_invalid_secret(payload_with_activated_account: dict) -> Request:
    """
    Create a request object with a JWT token signed with an incorrect secret.

    Returns:
        Request: A request object with a JWT token signed with an
                 incorrect secret in the Authorization header.
    """
    token = jwt.encode(payload_with_activated_account, "invalid_secret")
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
def token_request_with_invalid_algorithm(
    payload_with_activated_account: dict,
) -> Request:
    """
    Create a request object with a JWT token that has an invalid algorithm.

    Returns:
        Request: A request object with a JWT token that
                 specifies an invalid algorithm in the header.
    """

    # Encode the payload into a JWT token with the correct secret
    token = jwt.encode(payload_with_activated_account, FAKE_SECRET)

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
def request_with_blacklisted_token(payload_with_activated_account) -> Request:
    """
    Create a request object with a JWT token that is blacklisted.

    Returns:
        Request: A request object with a JWT token that has a JTI in the blacklist.
    """

    payload_with_activated_account["jti"] = JTI_IN_BLACKLIST

    token = jwt.encode(payload_with_activated_account, FAKE_SECRET)

    BlacklistTokenModel.objects.create(
        account_id=payload_with_activated_account["uid"],
        jti=payload_with_activated_account["jti"],
        exp=payload_with_activated_account["exp"],
        typ=payload_with_activated_account["typ"],
    )

    return Request(factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}"))


@pytest.fixture
def request_with_incorrect_type_token(payload_with_activated_account: dict) -> Request:
    """
    Create a request object with a JWT token with incorrect type token.
    """
    payload_with_activated_account["typ"] = INCORRECT_TYP

    token = jwt.encode(payload_with_activated_account, FAKE_SECRET)

    return Request(factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}"))


# ================ Tests =======================
@pytest.mark.django_db
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_authentication_fails_when_token_type_is_incorrect(
    request_with_incorrect_type_token: Request,
):
    """
    Test that authentication fails when the JWT token type ("typ") is incorrect.

    Args:
          request_with_incorrect_type_token (Request): The request fixture containing a
                                                     JWT token with an incorrect type.
    """
    expected_error_message = http_response.IS_NOT_ACCESS_TOKEN["detail"]
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
    expected_error_message = authentication.AUTHORIZATION_HEADER_MISSING
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
    expected_error_message = authentication.AUTHORIZATION_HEADER_WITHOUT_BEARER
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
    expected_error_message = authentication.INVALID_AUTHORIZATION_HEADER_FORMAT

    for request in incorrect_format_auth_header_request:
        with pytest.raises(AuthenticationFailed) as e:
            jwt_authentication.authenticate(request)

        assert expected_error_message == str(e.value)


@pytest.mark.django_db
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_authentication_fails_when_expired_token(expired_token_request: Request):
    """
    Test that authentication fails when the JWT is expired.

    Args:
        expired_token_request (Request): Request object with an expired
                                         JWT in the Authorization header.
    """
    expected_error_message = authentication.EXPIRED_SIGNATURE["detail"]
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(expired_token_request)

    assert expected_error_message == str(e.value)


@pytest.mark.django_db
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_authentication_fails_when_invalid_secret_token(
    token_request_with_invalid_secret: Request,
):
    """
    Test that authentication fails when the JWT has an invalid secret.

    Args:
        token_request_with_invalid_secret (Request): Request object with a JWT
                                                     encoded using an incorrect secret.
    """
    expected_error_message = authentication.INVALID_SIGNATURE["detail"]
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(token_request_with_invalid_secret)

    assert expected_error_message == str(e.value)


@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_authentication_fails_when_malformed_token(malformed_token_request: Request):
    """
    Test that authentication fails when the JWT is malformed.

    Args:
        malformed_token_request (Request): Request object with a malformed JWT.
    """
    expected_error_message = authentication.DECODE_ERROR["detail"]
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(malformed_token_request)

    assert expected_error_message == str(e.value)


@pytest.mark.django_db
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_authentication_fails_when_invalid_algorithm_token(
    token_request_with_invalid_algorithm: Request,
):
    """
    Test to ensure that authentication fails when the JWT uses an invalid algorithm.

    Args:
        token_request_with_invalid_algorithm (Request): Request object containing a
                                                        JWT with an invalid algorithm.
    """
    expected_error_message = authentication.INVALID_ALGORITHM["detail"]
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(token_request_with_invalid_algorithm)

    assert expected_error_message == str(e.value)


@pytest.mark.django_db
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_authentication_fails_when_blacklisted_token(
    request_with_blacklisted_token: Request,
):
    """
    Test that authentication fails when the JWT is blacklisted.

    Args:
        request_with_blacklisted_token (Request): Request object with a blacklisted JWT.
    """

    expected_error_message = authentication.TOKEN_IN_BLACKLIST["detail"]
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(request_with_blacklisted_token)

    assert expected_error_message == str(e.value)


@pytest.mark.django_db
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_authentication_fails_when_nonexistent_account(
    token_request_with_nonexistent_account: Request,
):
    """
    Test that authentication fails when the JWT is for a nonexistent account.

    Args:
        token_request_with_nonexistent_account (Request): Request object with a
                                                       JWT for a nonexistent account.
    """
    expected_error_message = http_response.ACCOUNT_NOT_FOUND["detail"]
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(token_request_with_nonexistent_account)

    assert expected_error_message == str(e.value)


@pytest.mark.django_db
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_authentication_success(
    token_request_with_activated_account: Request,
    activated_account,
    payload_with_activated_account: dict,
):
    """
    Test that the authentication succeeds for an activated account.

    Args:
        token_request_with_activated_account (Request): The request containing a
                                                     JWT for an activated account.
        activated_account (Account): The activated account instance.
        payload_with_activated_account (dict): The expected payload of the
                                            JWT for the activated account.

    Asserts:
        The authenticated account's details match the expected account, and the JWT
        payload is correct.
    """
    actual_account, actual_payload = jwt_authentication.authenticate(
        token_request_with_activated_account
    )

    assert activated_account.id == actual_account.id
    assert activated_account.first_name == actual_account.first_name
    assert activated_account.last_name == actual_account.last_name
    assert activated_account.email == actual_account.email
    assert activated_account.password == actual_account.password
    assert activated_account.is_active == actual_account.is_active
    assert payload_with_activated_account == actual_payload


@pytest.mark.django_db
@patch(f"{TOKEN_SERVICE_MODULE_PATH}.{TOKEN_SECRET_SETTING_TO_PATCH}", FAKE_SECRET)
def test_authentication_fails_when_account_deactivated(
    token_request_with_deactivated_account: Request,
):
    """
    Test that authentication fails when the account is deactivated.

    Args:
        token_request_with_deactivated_account (Request): The request containing a
                                                        JWT for a deactivated account.

    Asserts:
        The authentication fails with the appropriate error message
        indicating the account is not activated.
    """
    expected_error_message = http_response.ACCOUNT_NOT_ACTIVATED["detail"]
    with pytest.raises(AuthenticationFailed) as e:
        jwt_authentication.authenticate(token_request_with_deactivated_account)

    assert expected_error_message == str(e.value)
