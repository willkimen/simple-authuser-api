"""
Constants for TokenExceptions.
"""

# Errors for token exception in token_exceptions.py module.
DECODE_ERROR = {
    "code": "DECODE_ERROR",
    "detail": "Failed to decode the token. Please ensure the token is properly formatted.",
}

INVALID_TOKEN = {"code": "INVALID_TOKEN", "detail": "The token is invalid."}

INVALID_SIGNATURE = {
    "code": "INVALID_SIGNATURE",
    "detail": "The token signature is invalid.",
}
EXPIRED_SIGNATURE = {
    "code": "EXPIRED_SIGNATURE",
    "detail": "The token signature has expired.",
}

INVALID_ALGORITHM = {
    "code": "INVALID_ALGORITHM",
    "detail": "The algorithm specified is not supported or invalid. Please check the algorithm and try again.",
}

TOKEN_IN_BLACKLIST = {
    "code": "TOKEN_BLACKLISTED",
    "detail": "Token is blacklisted and therefore invalid",
}


"""
Error messages for JWT authentication.
These messages are used to provide feedback when authentication fails due to issues 
with the Authorization header.
The purpose is to centralize all error messages related to JWT authentication in 
one place for easier management and consistency.
"""

AUTHORIZATION_HEADER_MISSING = "Authorization header is missing"
INVALID_AUTHORIZATION_HEADER_FORMAT = (
    "Invalid Authorization header format. Authorization header must be: "
    "'Bearer <token>', separated by a space."
)
AUTHORIZATION_HEADER_WITHOUT_BEARER = "Authorization header must start with 'Bearer'."


# Expired token configuration
REFRESH_TOKEN_EXPIRATION_DAYS = 7
ACCESS_TOKEN_EXPIRATION_MINUTES = 10
