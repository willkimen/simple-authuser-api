"""
This module handles the creation, verification, and revocation of JWT tokens for account 
authentication. It contains functions for generating access and refresh tokens, 
verifying the validity of existing tokens, and revoking tokens by adding them to 
a blacklist. The generated tokens are signed with a secret key and have a 
configurable expiration time.

Main functions:
- Creation of JWT tokens (access and refresh).
- Verification of JWT token validity.
- Revocation of tokens, including adding non-expired tokens to the blacklist 
  and generating new tokens.
"""

import hashlib
import time
from datetime import datetime, timedelta

import jwt
from django.conf import settings
from django.db.models.query import QuerySet
from django.utils import timezone
from user_app.authentication.token_exceptions import (
    BlacklistTokenException,
    DecodeException,
    ExpiredSignatureException,
    InvalidAlgorithmException,
    InvalidSignatureException,
    InvalidTokenException,
)
from user_app.constants.authentication import (
    ACCESS_TOKEN_EXPIRATION_MINUTES,
    REFRESH_TOKEN_EXPIRATION_DAYS,
)
from user_app.models import BlacklistTokenModel, ValidTokenModel


def create_payload(id: int, is_refresh: bool = False) -> dict:
    """
    Create a JWT payload for an account.

    Args:
        id (int): The ID of the account.
        is_refresh (bool): Indicates whether the payload is for a refresh token.
                           If True, creates a refresh token payload; otherwise,
                           creates an access token payload.

    Returns:
        dict: The generated JWT payload.
    """

    # Create a unique JWT ID (JTI) using the account ID and the current timestamp.
    unix_timestamp = str(int(time.time()))
    hash = str(id) + unix_timestamp
    jti: str = hashlib.sha256(hash.encode()).hexdigest()

    # Create an expiration timestamp for the token.
    exp: float = (
        (timezone.now() + timedelta(days=REFRESH_TOKEN_EXPIRATION_DAYS)).timestamp()
        if is_refresh
        else (
            timezone.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRATION_MINUTES)
        ).timestamp()
    )

    return {
        "uid": id,
        "typ": "refresh" if is_refresh else "access",
        "jti": jti,
        "exp": int(exp),
    }


def create_token(id: int, is_refresh: bool = False) -> str:
    """
    Generates a JWT token for a given account.

    If `is_refresh` is set to True, a refresh token is generated
    and stored in the database else a access is generated and stored in database.
    Otherwise, an access token is created. Both tokens are signed using a secret key
    stored in the environment variable `TOKEN_SECRET`.

    Args:
        id (int): The ID of the account for whom the token is generated.
        is_refresh (bool, optional): Determines if the token is a refresh token.
        Defaults to False.

    Returns:
        str: The encoded JWT token.
    """

    payload: dict = create_payload(id, is_refresh)

    # Save the jti token in database
    ValidTokenModel.objects.create(
        account_id=id, jti=payload["jti"], exp=payload["exp"], typ=payload["typ"]
    )

    return jwt.encode(payload, settings.TOKEN_SECRET)


def create_pair_token(id: int) -> dict:
    """
    Create a pair of JWTs (access and refresh) for an account.

    Returns:
        dict: A dictionary containing the access and refresh JWTs.
    """

    return {
        "access": create_token(id),
        "refresh": create_token(id, is_refresh=True),
    }


def check_token(token: str) -> dict:
    """
    Check the validity of a JWT.

    Args:
        token (str): The JWT to be checked.

    Returns:
        dict: The decoded JWT payload if the token is valid.

    Raises:
        ExpiredSignatureException: If the token has expired.
        InvalidAlgorithmException: If the token's algorithm is invalid.
        InvalidSignatureException: If the token signature is invalid.
        DecodeException: If the token cannot be decoded.
        InvalidTokenException: If the token is invalid.
        BlacklistTokenException: If the token is found in the blacklist.
    """
    try:
        payload: dict = jwt.decode(
            jwt=token, key=settings.TOKEN_SECRET, algorithms=["HS256"]
        )
    except jwt.exceptions.ExpiredSignatureError:
        raise ExpiredSignatureException()
    except jwt.exceptions.InvalidAlgorithmError:
        raise InvalidAlgorithmException()
    except jwt.exceptions.InvalidSignatureError:
        raise InvalidSignatureException()
    except jwt.exceptions.DecodeError:
        raise DecodeException()
    except jwt.exceptions.InvalidTokenError:
        raise InvalidTokenException()

    if BlacklistTokenModel.objects.filter(jti=payload["jti"]).exists():
        raise BlacklistTokenException()

    return payload


def revoke_tokens(id: int) -> dict[str, str]:
    """
    Revokes both access and refresh tokens for an account and generates a new token pair.

    This function revokes all active  tokens that haven't yet expired by adding them to
    the blacklist. Afterward, it deletes all tokens associated with the account
    and generates a new token pair.

       Args:
           id (int): The ID of the account whose tokens are being revoked.

       Returns:
           dict[str, str]: A new pair of access and refresh tokens for the account.
    """

    # Finds all occurrences of unexpired refresh.
    now: datetime = timezone.now()
    tokens_not_expired: QuerySet = ValidTokenModel.objects.filter(
        account_id=id, exp__gt=now
    )

    # Insert all refreshes not expired in blacklist.
    if tokens_not_expired:
        [
            BlacklistTokenModel.objects.create(
                account_id=token.account_id, typ=token.typ, jti=token.jti, exp=token.exp
            )
            for token in tokens_not_expired
        ]

    # Delete all occurrences.
    ValidTokenModel.objects.filter(account_id=id).delete()

    # Create new token pair.
    return create_pair_token(id)
