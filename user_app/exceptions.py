from user_app.constants import jwt_error_messages


class JWTBlackListException(Exception):
    def __init__(self, message=None):
        if message is None:
            message = jwt_error_messages.JWT_IN_BLACKLIST
        super().__init__(message)
