import hashlib
import os
import time
from datetime import datetime, timedelta, timezone

import jwt

from user_app.exceptions import JWTBlackListException
from user_app.models import JWTBlackList

"""

No login, o client recebe um access e um refresh.
Com o refresh, o client vai pegando novos access, sempre que o access expirar.
O client vai poder pegar novos access ate que o refresh expirar, quando expirar, tera que fazer login novamente, o que ira gerar um novo par de access e refresh.

Processo de logout ira revogar tanto o access quanto refresh.
"""


def __create_jti(user_id: int) -> str:
    unix_timestamp = str(int(time.time()))
    hash = str(user_id) + unix_timestamp
    jti = hashlib.sha256(hash.encode()).hexdigest()

    return jti


def __create_exp(is_refresh: bool = False) -> int:
    if is_refresh is True:
        exp_date = datetime.now() + timedelta(weeks=1)
        return int(exp_date.timestamp())

    exp_date = datetime.now() + timedelta(minutes=10)
    return int(exp_date.timestamp())


def __create_payload(user_id: int, is_refresh: bool = False) -> dict:
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
    return jwt.encode(
        __create_payload(user_id, is_refresh=True), os.environ.get("ENV_JWT_SECRET")
    )


def create_access_jwt(user_id: int) -> str:
    return jwt.encode(__create_payload(user_id), os.environ.get("ENV_JWT_SECRET"))


def create_pair_jwt(user_id: int) -> dict:
    return {
        "access": create_access_jwt(user_id),
        "refresh": __create_refresh_jwt(user_id),
    }


def check_token(token: str) -> dict:
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
