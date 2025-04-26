"""
This module provides exceptions related to the JWT token.
"""

from user_app.constants import authentication


class TokenException(Exception):
    """
    Base class for JWT-related errors.

    This class serves as the parent for all custom JWT exceptions. It stores
    the error message (detail) and the associated error code (code) and
    provides methods to represent the error as a string or dictionary.

    Attributes:
        detail (str): The error message.
        code (str): The specific error code related to the JWT issue.
    """

    def __init__(self, detail: str = None, code: str = None) -> None:
        """
        Initializes the JWTError with an optional detail message and error code.

        Args:
            detail (str, optional): The error message.
            code (str, optional): The error code.
        """
        self.detail = detail
        self.code = code
        super().__init__(self.detail, self.code)

    def __str__(self) -> str:
        """
        Returns the error message as the string representation of the exception.
        """
        return self.detail

    def dict_repr(self) -> dict:
        """
        Returns a dictionary representation of the error.

        Returns:
            dict: A dictionary with 'code' and 'detail' keys.
        """
        return {"code": self.code, "detail": self.detail}


class ExpiredSignatureException(TokenException):
    """
    Exception raised when a JWT's signature has expired.

    This exception is raised when a token's 'exp' claim indicates that it has
    exceeded its valid time period.

    Attributes:
        detail (str): The error message indicating expiration.
        code (str): The specific error code related to expired signature.
    """

    def __init__(self) -> None:
        """
        Initializes the ExpiredSignatureError with default message and code.
        """
        self.detail: str = authentication.EXPIRED_SIGNATURE["detail"]
        self.code: str = authentication.EXPIRED_SIGNATURE["code"]
        super().__init__(self.detail, self.code)


class InvalidAlgorithmException(TokenException):
    """
    Exception raised when an invalid algorithm is used in the JWT.

    This error occurs when the algorithm used to sign or verify the JWT is
    not supported or expected.

    Attributes:
        detail (str): The error message indicating invalid algorithm.
        code (str): The specific error code related to invalid algorithm.
    """

    def __init__(self) -> None:
        """
        Initializes the InvalidAlgorithmError with default message and code.
        """
        self.detail: str = authentication.INVALID_ALGORITHM["detail"]
        self.code: str = authentication.INVALID_ALGORITHM["code"]
        super().__init__(self.detail, self.code)


class InvalidSignatureException(TokenException):
    """
    Exception raised when the JWT's signature is invalid.

    This error occurs if the token's signature does not match the expected
    value, indicating potential tampering.

    Attributes:
        detail (str): The error message indicating invalid signature.
        code (str): The specific error code related to invalid signature.
    """

    def __init__(self) -> None:
        """
        Initializes the InvalidSignatureError with default message and code.
        """
        self.detail: str = authentication.INVALID_SIGNATURE["detail"]
        self.code: str = authentication.INVALID_SIGNATURE["code"]
        super().__init__(self.detail, self.code)


class DecodeException(TokenException):
    """
    Exception raised when there is an error decoding the JWT.

    This error occurs when the token's structure or content is invalid,
    preventing successful decoding.

    Attributes:
        detail (str): The error message indicating decode failure.
        code (str): The specific error code related to decode error.
    """

    def __init__(self) -> None:
        """
        Initializes the DecodeError with default message and code.
        """
        self.detail: str = authentication.DECODE_ERROR["detail"]
        self.code: str = authentication.DECODE_ERROR["code"]
        super().__init__(self.detail, self.code)


class InvalidTokenException(TokenException):
    """
    Exception raised when the JWT is invalid.

    This error covers generic cases where a token is found to be invalid,
    such as malformed tokens, missing claims, etc.

    Attributes:
        detail (str): The error message indicating an invalid token.
        code (str): The specific error code related to invalid tokens.
    """

    def __init__(self) -> None:
        """
        Initializes the InvalidTokenError with default message and code.
        """
        self.detail: str = authentication.INVALID_TOKEN["detail"]
        self.code: str = authentication.INVALID_TOKEN["code"]
        super().__init__(self.detail, self.code)


class BlacklistTokenException(TokenException):
    """
    Exception raised when a JWT is found in the blacklist.

    This exception is used to signal that a token, identified by its
    'jti' (JWT ID), is present in the blacklist and is therefore invalid.
    The presence of a token in the blacklist means it has been revoked or
    is otherwise unauthorized for further use.

    Attributes:
        detail (str): The default error message indicating the token is blacklisted.
        code (str): A specific error code related to the blacklist violation.
    """

    def __init__(self) -> None:
        """
        Initialize the BlacklistTokenException with a default message and code.
        """
        self.detail: str = authentication.TOKEN_IN_BLACKLIST["detail"]
        self.code: str = authentication.TOKEN_IN_BLACKLIST["code"]
        super().__init__(self.detail, self.code)
