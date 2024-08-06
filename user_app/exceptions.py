from user_app.constants import jwt_error_messages


class JWTBlackListException(Exception):
    """
    Exception raised when a JWT is found in the blacklist.

    This exception is used to indicate that a token, identified by its
    'jti' (JWT ID), is present in the blacklist and therefore should
    not be accepted as valid.

    Attributes:
        message (str): The error message to be reported. If not provided,
                       a default message is used indicating that the JWT
                       is in the blacklist.
    """

    def __init__(self, message=None):
        """
        Initialize the JWTBlackListException with a specific message.

        Args:
            message (str, optional): The error message to be used. If None,
                                     a default message from jwt_error_messages
                                     will be used. Defaults to None.
        """
        if message is None:
            message = jwt_error_messages.JWT_IN_BLACKLIST
        super().__init__(message)
