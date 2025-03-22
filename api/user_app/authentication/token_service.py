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
from user_app.models import BlacklistTokenModel, ValidTokenModel

EXPIRATION_TIME_FOR_REFRESH = 1
EXPIRATION_TIME_FOR_ACCESS = 10


def create_payload(user_id: int, is_refresh: bool = False) -> dict:
    """
    Create a JWT payload for a user.

    Args:
        user_id (int): The ID of the user.
        is_refresh (bool): Indicates whether the payload is for a refresh token.
                           If True, creates a refresh token payload; otherwise,
                           creates an access token payload.

    Returns:
        dict: The generated JWT payload.
    """

    # Create a unique JWT ID (JTI) using the user ID and the current timestamp.
    unix_timestamp = str(int(time.time()))
    hash = str(user_id) + unix_timestamp
    jti: str = hashlib.sha256(hash.encode()).hexdigest()

    # Create an expiration timestamp for the token.
    exp: float = (
        (timezone.now() + timedelta(weeks=EXPIRATION_TIME_FOR_REFRESH)).timestamp()
        if is_refresh
        else (
            timezone.now() + timedelta(minutes=EXPIRATION_TIME_FOR_ACCESS)
        ).timestamp()
    )

    return {
        "uid": user_id,
        "typ": "refresh" if is_refresh else "access",
        "jti": jti,
        "exp": int(exp),
    }


def create_token(user_id: int, is_refresh: bool = False) -> str:
    """
    Generates a JWT token for a given user.

    If `is_refresh` is set to True, a refresh token is generated
    and stored in the database else a access is generated and stored in database.
    Otherwise, an access token is created. Both tokens are signed using a secret key
    stored in the environment variable `TOKEN_SECRET`.

    Args:
        user_id (int): The ID of the user for whom the token is generated.
        is_refresh (bool, optional): Determines if the token is a refresh token.
        Defaults to False.

    Returns:
        str: The encoded JWT token.
    """

    payload: dict = create_payload(user_id, is_refresh)

    # Save the jti token in database
    ValidTokenModel.objects.create(
        user_id=user_id, jti=payload["jti"], exp=payload["exp"], typ=payload["typ"]
    )

    return jwt.encode(payload, settings.TOKEN_SECRET)


def create_pair_token(user_id: int) -> dict:
    """
    Create a pair of JWTs (access and refresh) for a user.

    Returns:
        dict: A dictionary containing the access and refresh JWTs.
    """

    return {
        "access": create_token(user_id),
        "refresh": create_token(user_id, is_refresh=True),
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


def revoke_tokens(user_id: int) -> dict[str, str]:
    """
    Revokes both access and refresh tokens for a user and generates a new token pair.

    This function revokes all active  tokens that haven't yet expired by adding them to
    the blacklist. Afterward, it deletes all tokens associated with the user
    and generates a new token pair.

       Args:
           user_id (int): The ID of the user whose tokens are being revoked.

       Returns:
           dict[str, str]: A new pair of access and refresh tokens for the user.
    """

    # Finds all occurrences of unexpired refresh.
    now: datetime = timezone.now()
    tokens_not_expired: QuerySet = ValidTokenModel.objects.filter(
        user_id=user_id, exp__gt=now
    )

    # Insert all refreshes not expired in blacklist.
    if tokens_not_expired:
        [
            BlacklistTokenModel.objects.create(
                user_id=token.user_id, typ=token.typ, jti=token.jti, exp=token.exp
            )
            for token in tokens_not_expired
        ]

    # Delete all occurrences.
    ValidTokenModel.objects.filter(user_id=user_id).delete()

    # Create new token pair.
    return create_pair_token(user_id)
