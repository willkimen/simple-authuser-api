"""
This module provides views related to creating, updating, deleting and 
returning data for a given user.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.request import Request
from rest_framework.response import Response
from user_app.authentication.authentication_classes import JWTAuthentication
from user_app.authentication.token_service import revoke_tokens
from user_app.constants.response_codes_and_messages import (
    PASSWORD_INCORRECT,
    USER_DELETED_SUCCESSFULLY,
    USER_PASSWORD_CHANGED,
    USER_REGISTERED_SUCCESSFULLY,
    USER_UPDATED_SUCCESSFULLY,
    VALIDATION_ERRORS,
)
from user_app.documentation_scheme.authentication import authentication_errors_response
from user_app.documentation_scheme.profile import (
    password_validation_errors_and_incorrect_password_response,
    register_validation_errors_response,
    update_validation_errors_response,
    user_deleted_response,
    user_detail_response,
    user_password_changed_response,
    user_registered_response,
    user_updated_response,
)
from user_app.models.user_models import PendingAccountsModel
from user_app.serializers import (
    UserChangePasswordSerializer,
    UserRequestSerializer,
    UserResponseSerializer,
    UserUpdateSerializer,
)
from user_app.tasks import (
    task_notify_deleted_account,
    task_send_account_activation_code,
)
from user_app.utils import deep_merge_dict

User = get_user_model()


@extend_schema(
    request=UserRequestSerializer,
    responses={201: user_registered_response, 400: register_validation_errors_response},
)
@api_view(["POST"])
@authentication_classes([])
def register(request: Request) -> Response:
    """
    Registers a new user and sends an activation code via email.

    This view receives user registration data, validates it, and saves the user
    to the database. After successful registration, an activation code is sent
    to the user's email for account verification.

    Authentication:

        - Does not require authentication.
    """
    request_serializer = UserRequestSerializer(data=request.data)

    # Check if the provided data is valid.
    if not request_serializer.is_valid():
        return Response(
            deep_merge_dict(
                VALIDATION_ERRORS, {"field_errors": request_serializer.errors}
            ),
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Save the user to the database.
    user = request_serializer.save()

    # Send the activation code to user email address.
    task_send_account_activation_code.delay(request_serializer.validated_data["email"])

    # Creates a record in the PendingAccountsModel table for the newly registered user.
    # This ensures that the system tracks users who haven't activated their accounts
    # yet, so reminder emails can be sent and the account can be deleted if not
    # activated in time.
    PendingAccountsModel.objects.create(user=user)

    # Serialize the created user data using the response serializer.
    response_serializer = UserResponseSerializer(user)

    return Response(
        deep_merge_dict(
            USER_REGISTERED_SUCCESSFULLY, {"user": response_serializer.data}
        ),
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    request=UserUpdateSerializer,
    responses={
        200: user_updated_response,
        400: update_validation_errors_response,
        401: authentication_errors_response,
    },
)
@api_view(["PATCH"])
@authentication_classes([JWTAuthentication])
def update(request: Request) -> Response:
    """
    Partially updates the authenticated user's data.

    This view allows an authenticated user to update specific fields in their profile,
    such as first name and last name. Since this is a partial update, it is not
    necessary to provide all fields.

    Authentication:

        - The user must be authenticated using JWT tokens.

        - The token should be provided in the `Authorization` header as a Bearer token.
    """

    # Initialize the serializer with the current user instance and the provided data.
    # 'partial=True' allows partial updates
    # (only fields provided in the request will be updated).
    update_serializer = UserUpdateSerializer(
        instance=request.user, data=request.data, partial=True
    )

    # Check if the provided data is valid according to the serializer.
    if not update_serializer.is_valid():
        return Response(
            deep_merge_dict(
                VALIDATION_ERRORS, {"field_errors": update_serializer.errors}
            ),
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Save the updated user data to the database.
    user = update_serializer.save()

    # Serialize the updated user data to include in the response.
    response_serializer = UserResponseSerializer(user)

    # Return a success response with the updated user data.
    return Response(
        deep_merge_dict(USER_UPDATED_SUCCESSFULLY, {"user": response_serializer.data}),
        status=status.HTTP_200_OK,
    )


@extend_schema(
    request=None,
    responses={
        200: user_detail_response,
        401: authentication_errors_response,
    },
)
@api_view(["GET"])
@authentication_classes([JWTAuthentication])
def detail(request: Request) -> Response:
    """
    Returns the data of the authenticated user.

    This endpoint returns the profile information of the currently authenticated user.

    It does not require any parameters in the request body or query string.

    Authentication:

        - The user must be authenticated using JWT tokens.

        - The token should be provided in the `Authorization` header as a Bearer token.
    """
    response_serializer = UserResponseSerializer(request.user)
    return Response({"user": response_serializer.data}, status=status.HTTP_200_OK)


@extend_schema(
    request=None,
    responses={
        200: user_deleted_response,
        401: authentication_errors_response,
    },
)
@api_view(["DELETE"])
@authentication_classes([JWTAuthentication])
def delete(request: Request) -> Response:
    """
    Deletes the authenticated user from the system.

    This view permanently deletes the currently authenticated user's account and all
    associated data from the application. The user instance is retrieved via JWT
    authentication.

    It does not require any parameters in the request body or query string.

    Authentication:

        - The user must be authenticated using JWT tokens.

        - The token should be provided in the `Authorization` header as a Bearer token.
    """
    email: str = request.user.email
    request.user.delete()

    # Notify user about account deletion.
    task_notify_deleted_account.delay(email)

    return Response(USER_DELETED_SUCCESSFULLY, status=status.HTTP_200_OK)


@extend_schema(
    request=UserChangePasswordSerializer,
    responses={
        200: user_password_changed_response,
        400: password_validation_errors_and_incorrect_password_response,
        401: authentication_errors_response,
    },
)
@api_view(["PATCH"])
@authentication_classes([JWTAuthentication])
def change_password(request: Request) -> Response:
    """
    Allows an authenticated user to change their password.

    This endpoint enables a user to update their password by providing the
    current password (`actual_password`) and a new password (`new_password`).
    If the current password does not match the stored password, an error is returned.

    Revokes all existing tokens associated and returns a new pair of tokens
    (access and refresh).

    Authentication:

        - The user must be authenticated using JWT tokens.

        - The token should be provided in the `Authorization` header as a Bearer token.
    """

    serializer = UserChangePasswordSerializer(data=request.data)

    # Check if the provided data is valid according to the serializer.
    if not serializer.is_valid():
        return Response(
            deep_merge_dict(VALIDATION_ERRORS, {"field_errors": serializer.errors}),
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if the password coming from the request
    # is the same as that of the logged in user.
    if not check_password(serializer.data["actual_password"], request.user.password):
        return Response(PASSWORD_INCORRECT, status=status.HTTP_400_BAD_REQUEST)

    # Change and save new password for user.
    request.user.set_password(request.data["new_password"])
    request.user.save()

    # Revoke access token and all refreshes, and generate new token pair.
    token_pair: dict[str, str] = revoke_tokens(request.user.id)

    return Response(
        deep_merge_dict(USER_PASSWORD_CHANGED, token_pair), status=status.HTTP_200_OK
    )
