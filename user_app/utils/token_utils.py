import hashlib
import os
import time
from datetime import timedelta

import jwt
from django.utils import timezone

from user_app.exceptions import (
    BlacklistTokenException,
    DecodeException,
    ExpiredSignatureException,
    InvalidAlgorithmException,
    InvalidSignatureException,
    InvalidTokenException,
)
from user_app.models import BlacklistTokenModel, RefreshTokenModel

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
    jti = hashlib.sha256(hash.encode()).hexdigest()

    # Create an expiration timestamp for the token.
    exp = (
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
        "exp": exp,
    }


def create_token(user_id: int, is_refresh: bool = False):
    """
    Generates a JWT token for a given user.

    If `is_refresh` is set to True, a refresh token is generated
    and stored in the database.
    Otherwise, an access token is created. Both tokens are signed using a secret key
    stored in the environment variable `ENV_JWT_SECRET`.

    Args:
        user_id (int): The ID of the user for whom the token is generated.
        is_refresh (bool, optional): Determines if the token is a refresh token.
        Defaults to False.

    Returns:
        str: The encoded JWT token.
    """

    if is_refresh:
        payload = create_payload(user_id, is_refresh=True)

        # Save the jti refresh token in database
        RefreshTokenModel.objects.create(
            jti=payload["jti"], user_id=user_id, exp=payload["exp"]
        )

        return jwt.encode(payload, os.environ.get("ENV_JWT_SECRET"))

    return jwt.encode(create_payload(user_id), os.environ.get("ENV_JWT_SECRET"))


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
        payload = jwt.decode(
            jwt=token,
            key=os.environ.get("ENV_JWT_SECRET"),
            algorithms=["HS256"],
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
