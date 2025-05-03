"""
This module provides views related to creating, updating, deleting and 
returning data for a given account.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.request import Request
from rest_framework.response import Response
from account_auth.authentication.authentication_classes import JWTAuthentication
from account_auth.authentication.token_service import revoke_tokens
from account_auth.constants.http_response import (
    ACCOUNT_DELETED_SUCCESSFULLY,
    ACCOUNT_PASSWORD_CHANGED,
    ACCOUNT_REGISTERED_SUCCESSFULLY,
    ACCOUNT_UPDATED_SUCCESSFULLY,
    PASSWORD_INCORRECT,
    VALIDATION_ERRORS,
)
from account_auth.documentation_scheme.authentication import authentication_errors_response
from account_auth.documentation_scheme.profile import (
    account_deleted_response,
    account_detail_response,
    account_password_changed_response,
    account_registered_response,
    account_updated_response,
    password_validation_errors_and_incorrect_password_response,
    register_validation_errors_response,
    update_validation_errors_response,
)
from account_auth.models.account import PendingAccountsModel
from account_auth.serializers import (
    AccountChangePasswordSerializer,
    AccountRequestSerializer,
    AccountResponseSerializer,
    AccountUpdateSerializer,
)
from account_auth.tasks import (
    task_notify_deleted_account,
    task_send_account_activation_code,
)
from account_auth.utils import deep_merge_dict

Account = get_user_model()


@extend_schema(
    request=AccountRequestSerializer,
    responses={
        201: account_registered_response,
        400: register_validation_errors_response,
    },
)
@api_view(["POST"])
@authentication_classes([])
def register(request: Request) -> Response:
    """
    Registers a new account and sends an activation code via email.

    This view receives account registration data, validates it, and saves the account
    to the database. After successful registration, an activation code is sent
    to the account's email for account verification.

    Authentication:

        - Does not require authentication.
    """
    request_serializer = AccountRequestSerializer(data=request.data)

    # Check if the provided data is valid.
    if not request_serializer.is_valid():
        return Response(
            deep_merge_dict(
                VALIDATION_ERRORS, {"field_errors": request_serializer.errors}
            ),
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Save the account to the database.
    account = request_serializer.save()

    # Send the activation code to account email address.
    task_send_account_activation_code.delay(request_serializer.validated_data["email"])

    # Creates a record in the PendingAccountsModel table for the newly registered account.
    # This ensures that the system tracks accounts who haven't activated their accounts
    # yet, so reminder emails can be sent and the account can be deleted if not
    # activated in time.
    PendingAccountsModel.objects.create(account=account)

    # Serialize the created account data using the response serializer.
    response_serializer = AccountResponseSerializer(account)

    return Response(
        deep_merge_dict(
            ACCOUNT_REGISTERED_SUCCESSFULLY, {"account": response_serializer.data}
        ),
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    request=AccountUpdateSerializer,
    responses={
        200: account_updated_response,
        400: update_validation_errors_response,
        401: authentication_errors_response,
    },
)
@api_view(["PATCH"])
@authentication_classes([JWTAuthentication])
def update(request: Request) -> Response:
    """
    Partially updates the authenticated account's data.

    This view allows an authenticated account to update specific fields in their account,
    such as first name and last name. Since this is a partial update, it is not
    necessary to provide all fields.

    Authentication:

        - The account must be authenticated using JWT tokens.

        - The token should be provided in the `Authorization` header as a Bearer token.
    """

    # Initialize the serializer with the current account instance and the provided data.
    # 'partial=True' allows partial updates
    # (only fields provided in the request will be updated).
    update_serializer = AccountUpdateSerializer(
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

    # Save the updated account data to the database.
    account = update_serializer.save()

    # Serialize the updated account data to include in the response.
    response_serializer = AccountResponseSerializer(account)

    # Return a success response with the updated account data.
    return Response(
        deep_merge_dict(
            ACCOUNT_UPDATED_SUCCESSFULLY, {"account": response_serializer.data}
        ),
        status=status.HTTP_200_OK,
    )


@extend_schema(
    request=None,
    responses={
        200: account_detail_response,
        401: authentication_errors_response,
    },
)
@api_view(["GET"])
@authentication_classes([JWTAuthentication])
def detail(request: Request) -> Response:
    """
    Returns the data of the authenticated account.

    This endpoint returns the account information of the currently authenticated account.

    It does not require any parameters in the request body or query string.

    Authentication:

        - The account must be authenticated using JWT tokens.

        - The token should be provided in the `Authorization` header as a Bearer token.
    """
    response_serializer = AccountResponseSerializer(request.user)
    return Response({"account": response_serializer.data}, status=status.HTTP_200_OK)


@extend_schema(
    request=None,
    responses={
        200: account_deleted_response,
        401: authentication_errors_response,
    },
)
@api_view(["DELETE"])
@authentication_classes([JWTAuthentication])
def delete(request: Request) -> Response:
    """
    Deletes the authenticated account from the system.

    This view permanently deletes the currently authenticated account and all
    associated data from the application. The account instance is retrieved via JWT
    authentication.

    It does not require any parameters in the request body or query string.

    Authentication:

        - The account must be authenticated using JWT tokens.

        - The token should be provided in the `Authorization` header as a Bearer token.
    """
    email: str = request.user.email
    request.user.delete()

    # Notify account about account deletion.
    task_notify_deleted_account.delay(email)

    return Response(ACCOUNT_DELETED_SUCCESSFULLY, status=status.HTTP_200_OK)


@extend_schema(
    request=AccountChangePasswordSerializer,
    responses={
        200: account_password_changed_response,
        400: password_validation_errors_and_incorrect_password_response,
        401: authentication_errors_response,
    },
)
@api_view(["PATCH"])
@authentication_classes([JWTAuthentication])
def change_password(request: Request) -> Response:
    """
    Allows an authenticated account to change their password.

    This endpoint enables an account to update their password by providing the
    current password (`actual_password`) and a new password (`new_password`).
    If the current password does not match the stored password, an error is returned.

    Revokes all existing tokens associated and returns a new pair of tokens
    (access and refresh).

    Authentication:

        - The account must be authenticated using JWT tokens.

        - The token should be provided in the `Authorization` header as a Bearer token.
    """

    serializer = AccountChangePasswordSerializer(data=request.data)

    # Check if the provided data is valid according to the serializer.
    if not serializer.is_valid():
        return Response(
            deep_merge_dict(VALIDATION_ERRORS, {"field_errors": serializer.errors}),
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if the password coming from the request
    # is the same as that of the logged in account.
    if not check_password(serializer.data["actual_password"], request.user.password):
        return Response(PASSWORD_INCORRECT, status=status.HTTP_400_BAD_REQUEST)

    # Change and save new password for account.
    request.user.set_password(request.data["new_password"])
    request.user.save()

    # Revoke access token and all refreshes, and generate new token pair.
    token_pair: dict[str, str] = revoke_tokens(request.user.id)

    return Response(
        deep_merge_dict(ACCOUNT_PASSWORD_CHANGED, token_pair), status=status.HTTP_200_OK
    )
