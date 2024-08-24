from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from user_app.constants import authentication_error_messages, response_code_messages
from user_app.exceptions import JWTException
from user_app.utils.jwt_token import check_token

User = get_user_model()


class JWTAuthentication(BaseAuthentication):
    """
    Custom JWT authentication class for Django REST framework.

    This class provides a custom implementation of JWT authentication, verifying tokens in the
    Authorization header of requests. It handles token validation and user authentication.

    Attributes:
        www_authenticate_realm (str): The realm used in the WWW-Authenticate header for authentication challenges.
    """

    www_authenticate_realm = "api"

    def authenticate(self, request: Request) -> tuple | None:
        """
        Authenticate the request based on the JWT token provided in the Authorization header.

        Args:
            request (Request): The HTTP request object containing the Authorization header.

        Returns:
            tuple: A tuple of (user, payload) if authentication is successful.

        Raises:
            AuthenticationFailed: If the token is missing, malformed, expired, or invalid.
        """
        # Get the Authorization header and split it into parts: [Bearer, <jwt>]
        authorization_header: list[str] = get_authorization_header(request).split()

        # Check if the Authorization header is missing
        if not authorization_header:
            raise AuthenticationFailed(
                authentication_error_messages.AUTHORIZATION_HEADER_MISSING
            )

        # Check if the Authorization header does not start with 'Bearer'
        if authorization_header[0].lower() != b"bearer":
            raise AuthenticationFailed(
                authentication_error_messages.AUTHORIZATION_HEADER_WITHOUT_BEARER
            )

        # Check if the Authorization header does not have exactly two parts
        if len(authorization_header) != 2:
            raise AuthenticationFailed(
                authentication_error_messages.INVALID_AUTHORIZATION_HEADER_FORMAT
            )

        # Extract the token from the header
        token = authorization_header[1].decode()

        # Validate the token and get the payload
        try:
            payload = check_token(token)
        except JWTException as e:
            raise AuthenticationFailed(str(e))

        # Verify is token is access type
        if payload["typ"] != "access":
            raise AuthenticationFailed(
                response_code_messages.IS_NOT_ACCESS_TOKEN["detail"]
            )

        # Get the user from the payload
        try:
            user = User.objects.get(id=payload["uid"])
            if user.is_active is False:
                raise AuthenticationFailed(
                    response_code_messages.USER_ACCOUNT_NOT_ACTIVATED["detail"]
                )
        except User.DoesNotExist:
            raise AuthenticationFailed(response_code_messages.USER_NOT_FOUND["detail"])

        return (user, payload)

    def authenticate_header(self, request: Request) -> str:
        """
        Return the WWW-Authenticate header for use in authentication challenges.

        Args:
            request (Request): The HTTP request object.

        Returns:
            str: The WWW-Authenticate header string.
        """
        return f"Bearer realm='{self.www_authenticate_realm}'"
