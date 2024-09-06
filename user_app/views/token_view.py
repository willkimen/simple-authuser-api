from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response

from user_app.authentication_classes import JWTAuthentication
from user_app.constants.response_code_messages import (
    IS_NOT_ACCESS_OR_REFRESH_TOKEN,
    IS_NOT_REFRESH_TOKEN,
    LOGIN_SUCCESSFUL,
    LOGOUT_SUCCESSFUL,
    TOKEN_ACCESS_CREATED,
    USER_ACCOUNT_NOT_ACTIVATED,
    USER_NOT_FOUND,
    USER_TOKEN_MISMATCH,
)
from user_app.exceptions import JWTBlackListException, JWTException
from user_app.models import JWTBlacklistModel
from user_app.utils.data_utils import merge_dict
from user_app.utils.token_utils import check_token, create_access_jwt, create_pair_jwt

User = get_user_model()


@api_view(["POST"])
def obtain_token_pair(request):
    """
    Handles user login and returns JWT tokens upon successful authentication.

    This endpoint is used for user login by validating the provided email and password.
    Upon successful authentication, it generates and returns a pair of JWT tokens (access and refresh).
    If the authentication fails or the user is not activated, appropriate error messages are returned.

    Args:
        request (Request): The HTTP request object containing the user's email and password.

    Returns:
        Response: An HTTP response object containing either the JWT tokens and success message or an error message.

    Response Codes:
        - 200 OK: Successfully authenticated the user and returned the JWT tokens.
        - 403 Forbidden: The user account is not activated.
        - 404 Not Found: The user with the provided email and password does not exist.
    """
    email = request.data.get("email", None)
    password = request.data.get("password", None)

    # Verify if user exists
    try:
        user = User.objects.get(email=email, password=password)
    except User.DoesNotExist:
        return Response(
            USER_NOT_FOUND,
            status=status.HTTP_404_NOT_FOUND,
        )

    # Verify if user has activated account
    if user.is_active is False:
        return Response(
            USER_ACCOUNT_NOT_ACTIVATED,
            status=status.HTTP_403_FORBIDDEN,
        )

    return Response(
        merge_dict(LOGIN_SUCCESSFUL, create_pair_jwt(user.id)),
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def refresh_token_access(request):
    """
    Refreshes the JWT access token using a valid refresh token.

    This endpoint accepts a POST request with a refresh token and performs the following actions:
    1. **Check Token Validity:** Verifies the provided refresh token. If the token is blacklisted or invalid, it returns an appropriate error response.
    2. **Validate Token Type:** Ensures that the token type is "refresh". If not, it returns a bad request error.
    3. **Verify User Existence:** Checks if the user associated with the token exists. If the user does not exist, it returns a not found error.
    4. **Check Account Activation:** Validates that the user's account is activated. If the account is not activated, it returns a forbidden error.
    5. **Generate New Access Token:** If all validations pass, it generates a new access token and returns it in the response along with a success message.

    Args:
        request (Request): The HTTP request object containing the refresh token.

    Returns:
        Response: The HTTP response object containing either the new access token or an error message.

    Response Codes:
        - 201 Created: Successfully generated a new access token.
        - 400 Bad Request: The token is not a refresh token or the token is invalid.
        - 403 Forbidden: The token is blacklisted or the user account is not activated.
        - 404 Not Found: The user associated with the token does not exist.
    """
    refresh = request.data.get("refresh", None)

    try:
        payload = check_token(refresh)
    except JWTBlackListException as e:
        return Response(e.dict_repr(), status=status.HTTP_403_FORBIDDEN)
    except JWTException as e:
        return Response(e.dict_repr(), status=status.HTTP_400_BAD_REQUEST)

    # Verify if token is a refresh type
    if payload["typ"] != "refresh":
        return Response(IS_NOT_REFRESH_TOKEN, status=status.HTTP_400_BAD_REQUEST)

    # Verify if user exists
    try:
        user = User.objects.get(id=payload["uid"])
    except User.DoesNotExist:
        return Response(
            USER_NOT_FOUND,
            status=status.HTTP_404_NOT_FOUND,
        )

    # Verify if user has activated account
    if user.is_active is False:
        return Response(
            USER_ACCOUNT_NOT_ACTIVATED,
            status=status.HTTP_403_FORBIDDEN,
        )

    return Response(
        merge_dict(TOKEN_ACCESS_CREATED, {"access": create_access_jwt(payload["uid"])}),
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
def blacklist_token(request):
    """
    Handles the blacklisting of a JWT token, preventing future use.

    This view performs the following actions:
    1. Validates the token by decoding its payload.
    2. Verifies if the token is of type 'access' or 'refresh'.
    3. Ensures that the authenticated user matches the token's owner.
    4. Blacklists the token by saving its 'jti' (JWT ID), 'exp' (expiration time), and 'typ' (type) in the database.

    Args:
        request (Request): The HTTP request, expected to contain a JWT token in the body.

    Returns:
        Response: A JSON response with the appropriate success or error message, and the corresponding HTTP status code.
    """
    token = request.data.get("token", None)

    try:
        payload = check_token(token)
    except JWTBlackListException as e:
        return Response(e.dict_repr(), status=status.HTTP_403_FORBIDDEN)
    except JWTException as e:
        return Response(e.dict_repr(), status=status.HTTP_400_BAD_REQUEST)

    # Verify if token is a refresh or access type
    if payload["typ"] not in ["access", "refresh"]:
        return Response(
            IS_NOT_ACCESS_OR_REFRESH_TOKEN, status=status.HTTP_400_BAD_REQUEST
        )

    # Verify that the authenticated user matches the token's owner.
    if request.user.id != payload["uid"]:
        return Response(USER_TOKEN_MISMATCH, status=status.HTTP_403_FORBIDDEN)

    # Insert the JTI token in blacklist
    JWTBlacklistModel.objects.create(
        jti=payload["jti"],
        exp=payload["exp"],
        typ=payload["typ"],
    )

    return Response(LOGOUT_SUCCESSFUL, status=status.HTTP_200_OK)
