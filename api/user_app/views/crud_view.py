"""
This module provides views related to creating, updating, deleting and 
returning data for a given user.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from user_app.authentication_classes import JWTAuthentication
from user_app.constants.response_codes_and_messages import (
    PASSWORD_DO_NOT_MATCH,
    USER_DELETED_SUCCESSFULLY,
    USER_PASSWORD_CHANGED,
    USER_REGISTERED_SUCCESSFULLY,
    USER_UPDATED_SUCCESSFULLY,
    VALIDATION_ERRORS,
)
from user_app.serializers import (
    UserChangePasswordSerializer,
    UserRequestSerializer,
    UserResponseSerializer,
    UserUpdateSerializer,
)
from user_app.tasks import task_send_activation_code_by_email
from user_app.utils.data_utils import merge_dict
from user_app.utils.token_utils import revoke_tokens

User = get_user_model()


@api_view(["POST"])
def register(request):
    """
    Registers a new user in the system and sends a code to the
    user's email address to activate the account.
    """
    request_serializer = UserRequestSerializer(data=request.data)

    # Check if the provided data is valid
    if not request_serializer.is_valid():
        return Response(
            merge_dict(VALIDATION_ERRORS, {"field_errors": request_serializer.errors}),
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Send the activation email
    task_send_activation_code_by_email.delay(request_serializer.validated_data["email"])

    # Save the user to the database
    user = request_serializer.save()

    # Serialize the created user data using the response serializer
    response_serializer = UserResponseSerializer(user)

    return Response(
        merge_dict(USER_REGISTERED_SUCCESSFULLY, {"user": response_serializer.data}),
        status=status.HTTP_201_CREATED,
    )


@api_view(["PATCH"])
@authentication_classes([JWTAuthentication])
def update(request):
    """
    Partially updates user data in the database. This user must be authenticated.
    """

    # Initialize the serializer with the current user instance and the provided data.
    # 'partial=True' allows partial updates
    # (only fields provided in the request will be updated).
    update_serializer = UserUpdateSerializer(
        instance=request.user, data=request.data, partial=True
    )

    # Check if the provided data is valid according to the serializer.
    if not update_serializer.is_valid():
        # If data is invalid, return a response with validation errors.
        return Response(
            merge_dict(VALIDATION_ERRORS, {"field_errors": update_serializer.errors}),
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Save the updated user data to the database.
    user = update_serializer.save()

    # Serialize the updated user data to include in the response.
    response_serializer = UserResponseSerializer(user)

    # Return a success response with the updated user data.
    return Response(
        merge_dict(USER_UPDATED_SUCCESSFULLY, {"user": response_serializer.data}),
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
def user_detail(request):
    """
    Returns authenticated user data.
    """
    response_serializer = UserResponseSerializer(request.user)
    return Response({"user": response_serializer.data}, status=status.HTTP_200_OK)


@api_view(["DELETE"])
@authentication_classes([JWTAuthentication])
def delete(request):
    """
    Deletes the authenticated user.
    """
    request.user.delete()
    return Response(USER_DELETED_SUCCESSFULLY, status=status.HTTP_200_OK)


@api_view(["PATCH"])
@authentication_classes([JWTAuthentication])
def change_password(request):
    """
    Allows a user to change their password.

    This endpoint requires the user to be authenticated with a JWT token. It accepts
    PATCH requests containing the current password and the new password. If the
    provided current password does not match the stored password, an error is returned.

    Request Body:
    - actual_password: The user's current password.
    - new_password: The new password the user wants to set.
    """
    serializer = UserChangePasswordSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            merge_dict(VALIDATION_ERRORS, {"field_errors": serializer.errors}),
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if the password coming from the request
    # is the same as that of the logged in user.
    if not check_password(serializer.data["actual_password"], request.user.password):
        return Response(PASSWORD_DO_NOT_MATCH, status=status.HTTP_400_BAD_REQUEST)

    # Change and save new password for user.
    request.user.set_password(request.data["new_password"])
    request.user.save()

    # Revoke access token and all refreshes, and generate new token pair.
    token_pair: dict[str, str] = revoke_tokens(request.user.id)

    return Response(
        merge_dict(USER_PASSWORD_CHANGED, token_pair), status=status.HTTP_200_OK
    )
