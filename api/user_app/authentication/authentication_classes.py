from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from user_app.authentication.token_exceptions import TokenException
from user_app.authentication.token_service import check_token
from user_app.constants import authentication, http_response

Account = get_user_model()


class JWTAuthentication(BaseAuthentication):
    """
    Custom JWT authentication class for Django Rest Framework.

    This class extends BaseAuthentication to authenticate accounts using
    JSON Web Tokens (JWT).
    It extracts the token from the Authorization header of the request and
    performs multiple checks to validate its authenticity.
    If the token is valid, it returns a tuple containing the authenticated
    account instance and the token payload.

    To access the authenticated account instance in a view, use `request.account`.
    To access the token payload, use `request.auth`.
    """

    www_authenticate_realm = "api"

    def authenticate(self, request: Request) -> tuple | None:
        """
        Authenticate the request based on the JWT token provided
        in the Authorization header.

        Args:
            request (Request): The HTTP request object containing
                               the Authorization header.

        Returns:
            tuple: A tuple of (account, payload) if authentication is successful.

        Raises:
            AuthenticationFailed: If the token is missing, malformed, expired,
                                  or invalid.
        """

        # Get the Authorization header and split it into parts: [Bearer, <jwt>]
        authorization_header: list[str] = get_authorization_header(request).split()

        # Check if the Authorization header is missing
        if not authorization_header:
            raise AuthenticationFailed(authentication.AUTHORIZATION_HEADER_MISSING)

        # Check if the Authorization header does not start with 'Bearer'
        if authorization_header[0].lower() != b"bearer":
            raise AuthenticationFailed(
                authentication.AUTHORIZATION_HEADER_WITHOUT_BEARER
            )

        # Check if the Authorization header does not have exactly two parts
        if len(authorization_header) != 2:
            raise AuthenticationFailed(
                authentication.INVALID_AUTHORIZATION_HEADER_FORMAT
            )

        # Extract the token from the header
        token = authorization_header[1].decode()

        # Validate the token and get the payload
        try:
            payload: dict = check_token(token)
        except TokenException as e:
            raise AuthenticationFailed(str(e))

        # Verify is token is access type
        if payload["typ"] != "access":
            raise AuthenticationFailed(http_response.IS_NOT_ACCESS_TOKEN["detail"])

        # Get the account from the payload
        try:
            user = Account.objects.get(id=payload["uid"])
            if user.is_active is False:
                raise AuthenticationFailed(
                    http_response.ACCOUNT_NOT_ACTIVATED["detail"]
                )
        except Account.DoesNotExist:
            raise AuthenticationFailed(http_response.ACCOUNT_NOT_FOUND["detail"])

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
