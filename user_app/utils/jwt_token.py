import hashlib
import os
import time
from datetime import datetime, timedelta, timezone

import jwt

from user_app.exceptions import JWTBlackListException
from user_app.models import JWTBlackList


def __create_jti(user_id: int) -> str:
    """
    Create a unique JWT ID (JTI) using the user ID and the current timestamp.
    """
    unix_timestamp = str(int(time.time()))
    hash = str(user_id) + unix_timestamp
    jti = hashlib.sha256(hash.encode()).hexdigest()

    return jti


def __create_exp(is_refresh: bool = False) -> int:
    """
    Create an expiration timestamp for a token.

    Args:
        is_refresh (bool): Indicates whether the expiration is for a refresh token.
                           If True, sets expiration to one week; otherwise, sets to 10 minutes.

    Returns:
        int: The expiration timestamp.
    """
    if is_refresh is True:
        exp_date = datetime.now() + timedelta(weeks=1)
        return int(exp_date.timestamp())

    exp_date = datetime.now() + timedelta(minutes=10)
    return int(exp_date.timestamp())


def __create_payload(user_id: int, is_refresh: bool = False) -> dict:
    """
    Create a JWT payload for a user.

    Args:
        user_id (int): The ID of the user.
        is_refresh (bool): Indicates whether the payload is for a refresh token.
                           If True, creates a refresh token payload; otherwise, creates an access token payload.

    Returns:
        dict: The generated JWT payload.
    """
    if is_refresh:
        return {
            "uid": user_id,
            "typ": "refresh",
            "jti": __create_jti(user_id),
            "exp": __create_exp(is_refresh=True),
        }

    return {
        "uid": user_id,
        "typ": "access",
        "jti": __create_jti(user_id),
        "exp": __create_exp(),
    }


def __create_refresh_jwt(user_id: int) -> str:
    """
    Create a refresh JWT for a user.

    Returns:
        str: The encoded refresh JWT.
    """
    return jwt.encode(
        __create_payload(user_id, is_refresh=True), os.environ.get("ENV_JWT_SECRET")
    )


def create_access_jwt(user_id: int) -> str:
    """
    Create a access JWT for a user.

    Returns:
        str: The encoded access JWT.
    """
    return jwt.encode(__create_payload(user_id), os.environ.get("ENV_JWT_SECRET"))


def create_pair_jwt(user_id: int) -> dict:
    """
    Create a pair of JWTs (access and refresh) for a user.

    Returns:
        dict: A dictionary containing the access and refresh JWTs.
    """
    return {
        "access": create_access_jwt(user_id),
        "refresh": __create_refresh_jwt(user_id),
    }


def check_token(token: str) -> dict:
    """
    Check the validity of a JWT.

    Args:
        token (str): The JWT to be checked.

    Returns:
        dict: The decoded JWT payload if the token is valid.

    Raises:
        jwt.exceptions.ExpiredSignatureError: If the token has expired.
        jwt.exceptions.InvalidAlgorithmError: If the token's algorithm is invalid.
        jwt.exceptions.MissingRequiredClaimError: If the token is missing required claims.
        jwt.exceptions.InvalidSignatureError: If the token signature is invalid.
        jwt.exceptions.DecodeError: If the token cannot be decoded.
        jwt.exceptions.InvalidTokenError: If the token is invalid.
        JWTBlackListException: If the token is found in the blacklist.
    """
    try:
        payload = jwt.decode(
            jwt=token, key=os.environ.get("ENV_JWT_SECRET"), algorithms=["HS256"]
        )
    except jwt.exceptions.ExpiredSignatureError:
        raise jwt.exceptions.ExpiredSignatureError()
    except jwt.exceptions.InvalidSignatureError:
        raise jwt.exceptions.InvalidTokenError()
    except jwt.exceptions.DecodeError:
        raise jwt.exceptions.DecodeError()
    except jwt.exceptions.InvalidTokenError:
        raise jwt.exceptions.InvalidTokenError()

    if JWTBlackList.objects.filter(jti=payload["jti"]).exists():
        raise JWTBlackListException()

    return payload
