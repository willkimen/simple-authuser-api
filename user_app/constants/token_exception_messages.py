"""
Constants for JWTExceptions.
"""

DECODE_ERROR = {
    "code": "DECODE_ERROR",
    "detail": "Failed to decode the JWT token. Please ensure the token is properly formatted.",
}

INVALID_TOKEN = {"code": "INVALID_TOKEN", "detail": "The JWT token is invalid."}

INVALID_SIGNATURE = {
    "code": "INVALID_SIGNATURE",
    "detail": "The JWT token signature is invalid.",
}
EXPIRED_SIGNATURE = {
    "code": "EXPIRED_SIGNATURE",
    "detail": "The JWT token signature has expired.",
}

INVALID_ALGORITHM = {
    "code": "INVALID_ALGORITHM",
    "detail": "The algorithm specified is not supported or invalid. Please check the algorithm and try again.",
}

JWT_IN_BLACKLIST = {
    "code": "JWT_BLACKLISTED",
    "detail": "JWT is blacklisted and therefore invalid",
}
