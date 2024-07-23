class JWTBlackListException(Exception):
    def __init__(self, message=None):
        if message is None:
            message = "JWT is blacklisted and therefore invalid"
        super().__init__(message)
