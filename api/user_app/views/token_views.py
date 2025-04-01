"""
This module deals with views related to token manipulation.
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.request import Request
from rest_framework.response import Response
from user_app.authentication.authentication_classes import JWTAuthentication
from user_app.authentication.token_exceptions import (
    BlacklistTokenException,
    TokenException,
)
from user_app.authentication.token_service import (
    check_token,
    create_pair_token,
    create_token,
)
from user_app.constants.response_codes_and_messages import (
    IS_NOT_ACCESS_OR_REFRESH_TOKEN,
    IS_NOT_REFRESH_TOKEN,
    LOGIN_SUCCESSFUL,
    LOGOUT_SUCCESSFUL,
    TOKEN_ACCESS_CREATED,
    TOKEN_IS_VALID,
    USER_ACCOUNT_NOT_ACTIVATED,
    USER_NOT_FOUND,
    USER_TOKEN_MISMATCH,
)
from user_app.models import BlacklistTokenModel
from user_app.utils import merge_dict

User = get_user_model()


@api_view(["POST"])
def obtain_token_pair(request: Request) -> Response:
    """
    Authenticates a user and returns a pair of tokens.

    This view receives the user's email and password, verifies if the credentials
    are correct and if the account is active. If authentication is successful,
    it returns a pair of tokens (access and refresh) for the user.

    Request Body:
        {
            "email": "user@example.com",
            "password": "user_password"
        }
    """

    email: str | None = request.data.get("email", None)
    password: str | None = request.data.get("password", None)

    # Verify if user exists
    try:
        user = User.objects.get(email=email, password=password)
    except User.DoesNotExist:
        return Response(USER_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

    # Verify if user has activated account
    if user.is_active is False:
        return Response(USER_ACCOUNT_NOT_ACTIVATED, status=status.HTTP_403_FORBIDDEN)

    return Response(
        merge_dict(LOGIN_SUCCESSFUL, create_pair_token(user.id)),
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def refresh_token_access(request: Request) -> Response:
    """
    Generates a new access token using a valid refresh token.

    This view receives a refresh token, validates it, and returns a new access token.
    It ensures that the token is of type 'refresh' and belongs to an existing,
    active user.

    Request Body:
        {
            "refresh": "refresh_token"
        }
    """
    refresh: str | None = request.data.get("refresh", None)

    # Verify if the token is valid, it returns its payload.
    try:
        payload: dict = check_token(refresh)
    except BlacklistTokenException as e:
        return Response(e.dict_repr(), status=status.HTTP_403_FORBIDDEN)
    except TokenException as e:
        return Response(e.dict_repr(), status=status.HTTP_400_BAD_REQUEST)

    # Verify if token is a refresh type
    if payload["typ"] != "refresh":
        return Response(IS_NOT_REFRESH_TOKEN, status=status.HTTP_400_BAD_REQUEST)

    # Verify if user exists
    try:
        user = User.objects.get(id=payload["uid"])
    except User.DoesNotExist:
        return Response(USER_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

    # Checks if the user does not have an activated account
    if user.is_active is False:
        return Response(USER_ACCOUNT_NOT_ACTIVATED, status=status.HTTP_403_FORBIDDEN)

    return Response(
        merge_dict(TOKEN_ACCESS_CREATED, {"access": create_token(payload["uid"])}),
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
def blacklist_token(request: Request) -> Response:
    """
    Adds a token to the blacklist, preventing its future use.

    This view receives an access or refresh token, validates it, and adds it to
    the blacklist to ensure it can no longer be used. It also verifies that the
    authenticated user matches the token's owner.

    Request Body:
        {
            "token": "access_or_refresh_token"
        }
    """

    token: str | None = request.data.get("token", None)

    # Verify if the token is valid, it returns its payload.
    try:
        payload: dict = check_token(token)
    except BlacklistTokenException as e:
        return Response(e.dict_repr(), status=status.HTTP_403_FORBIDDEN)
    except TokenException as e:
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
    BlacklistTokenModel.objects.create(
        user_id=request.user.id,
        jti=payload["jti"],
        exp=payload["exp"],
        typ=payload["typ"],
    )

    return Response(LOGOUT_SUCCESSFUL, status=status.HTTP_200_OK)


@api_view(["POST"])
def verify_token(request: Request) -> Response:
    """
    Validates a given token and checks if it is still usable.

    This view receives an access or refresh token, verifies its validity,
    and ensures that it is not blacklisted. If the token is valid,
    a confirmation response is returned.

    Request Body:
        {
            "token": "access_or_refresh_token"
        }
    """
    token: str | None = request.data.get("token", None)

    # Verify if the token is valid, it returns its payload.
    try:
        payload: dict = check_token(token)
    except BlacklistTokenException as e:
        return Response(e.dict_repr(), status=status.HTTP_403_FORBIDDEN)
    except TokenException as e:
        return Response(e.dict_repr(), status=status.HTTP_400_BAD_REQUEST)

    # Verify if token is a refresh or access type
    if payload["typ"] not in ["access", "refresh"]:
        return Response(
            IS_NOT_ACCESS_OR_REFRESH_TOKEN, status=status.HTTP_400_BAD_REQUEST
        )

    return Response(TOKEN_IS_VALID, status=status.HTTP_200_OK)
