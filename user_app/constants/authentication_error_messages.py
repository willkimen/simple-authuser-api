"""
Error messages for JWT authentication.
These messages are used to provide feedback when authentication fails due to issues with the Authorization header.
The purpose is to centralize all error messages related to JWT authentication in one place for easier management and consistency.
"""

AUTHORIZATION_HEADER_MISSING = "Authorization header is missing"
INVALID_AUTHORIZATION_HEADER_FORMAT = "Invalid Authorization header format. Authorization header must be: 'Bearer <token>', separated by a space."
AUTHORIZATION_HEADER_WITHOUT_BEARER = "Authorization header must start with 'Bearer'."
