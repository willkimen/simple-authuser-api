import copy
import smtplib
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.utils.timezone import make_aware
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, throttle_classes
from rest_framework.response import Response

from user_app.authentication_classes import JWTAuthentication
from user_app.constants import confirmation_type_code
from user_app.constants.response_code_messages import (
    ACCOUNT_ACTIVATION_CODE_NOT_FOUND,
    CODE_FIELD_IS_REQUIRED,
    CONFIRMATION_CODE_EXPIRED,
    EMAIL_SEND_TO_USER_SUCCESSFULLY,
    ERROR_SENDING_EMAIL,
    INVALID_CONFIRMATION_CODE_TYPE,
    IS_NOT_REFRESH_JWT,
    JWT_ACCESS_CREATED,
    LOGIN_SUCCESSFUL,
    LOGOUT_SUCCESSFUL,
    USER_ACCOUNT_NOT_ACTIVATED,
    USER_ACTIVATED,
    USER_HAS_ALREADY_ACTIVATED,
    USER_NOT_FOUND,
    USER_REGISTERED_SUCCESSFULLY,
    USER_UPDATED_SUCCESSFULLY,
    VALIDATION_ERRORS,
)
from user_app.exceptions import JWTBlackListException, JWTException
from user_app.models import ConfirmationCode, JWTBlackList
from user_app.serializers import EmailSerializer, UserSerializer
from user_app.throttlings import (
    AccountActivationRequestRateLimit,
    SendEmailActivateAccountRequestRateLimit,
)
from user_app.utils.email_service import send_activation_code_by_email
from user_app.utils.jwt_token import check_token, create_access_jwt, create_pair_jwt

User = get_user_model()


@api_view(["POST"])
def register(request):
    """
    Registers a new user.

    This endpoint registers a new user in the system. If the provided data is valid,
    the user is created and an activation email is sent to the provided email address.
    The user is initially marked as inactive until they activate their account through the activation email.
    """
    serializer = UserSerializer(data=request.data)

    # Check if the provided data is valid
    if not serializer.is_valid():
        return Response(
            __merge_dict(VALIDATION_ERRORS, {"field_errors": serializer.errors}),
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Send the activation email
    try:
        send_activation_code_by_email(serializer.validated_data["email"])
    except smtplib.SMTPException as e:
        return Response(
            __merge_dict(ERROR_SENDING_EMAIL, {"error": str(e)}),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Save the user to the database
    serializer.save()

    return Response(
        __merge_dict(USER_REGISTERED_SUCCESSFULLY, {"user": serializer.data}),
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
def obtain_jwt_pair(request):
    """
    Handle user login by email and password.

    Args:
        request (Request): The request object containing email and password.

    Returns:
        Response: A response object containing JWT tokens if successful or an error message if failed.
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
        __merge_dict(LOGIN_SUCCESSFUL, create_pair_jwt(user.id)),
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def refresh_jwt_access(request):
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
        return Response(IS_NOT_REFRESH_JWT, status=status.HTTP_400_BAD_REQUEST)

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
        __merge_dict(JWT_ACCESS_CREATED, {"access": create_access_jwt(payload["uid"])}),
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
def blacklist_jwt_pair(request): ...


@api_view(["POST"])
def blacklist_jwt_access(request): ...


@api_view(["POST"])
def blacklist_jwt_refresh(request):
    JWTBlackList.objects.create(
        jti=request.auth["jti"],
        exp=request.auth["exp"],
        typ=request.auth["typ"],
    )

    return Response(LOGOUT_SUCCESSFUL, status=status.HTTP_200_OK)


@api_view(["PATCH"])
@authentication_classes([JWTAuthentication])
def update(request):

    serializer = UserSerializer(instance=request.user, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(
            __merge_dict(VALIDATION_ERRORS, {"field_errors": serializer.errors}),
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer.save()
    return Response(
        __merge_dict(USER_UPDATED_SUCCESSFULLY, {"user": serializer.data}),
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@throttle_classes([AccountActivationRequestRateLimit])
def activate_account(request):
    """
    Verify code and activates the user account.
    """
    code = request.data.get("code", None)

    # Checks if code field was sent by the request
    if code is None:
        return Response(
            CODE_FIELD_IS_REQUIRED,
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Convert to string if the type is different
    if not isinstance(code, str):
        code = str(code)

    # Checks if code exists in the data base
    try:
        confirmation_code = ConfirmationCode.objects.get(code=code)
    except ConfirmationCode.DoesNotExist:
        return Response(
            ACCOUNT_ACTIVATION_CODE_NOT_FOUND,
            status=status.HTTP_404_NOT_FOUND,
        )

    # Checks if type code is the correct
    if confirmation_code.type_code != confirmation_type_code.ACCOUNT_ACTIVATION:
        return Response(
            INVALID_CONFIRMATION_CODE_TYPE,
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Checks if the code is expired
    expired = timedelta(days=1)
    now = make_aware(datetime.now())
    if (now - confirmation_code.created_at) >= expired:
        confirmation_code.delete()
        return Response(
            CONFIRMATION_CODE_EXPIRED,
            status=status.HTTP_410_GONE,
        )

    # Activate user and save in the database
    user = User.objects.get(email=confirmation_code.user_email)
    user.is_active = True
    user.save()
    confirmation_code.delete()
    return Response(USER_ACTIVATED, status=status.HTTP_200_OK)


@api_view(["POST"])
@throttle_classes([SendEmailActivateAccountRequestRateLimit])
def send_email_to_activate_account(request):
    serializer = EmailSerializer(data=request.data)

    # Check if the provided data is valid
    if not serializer.is_valid():
        return Response(
            __merge_dict(VALIDATION_ERRORS, {"field_errors": serializer.errors}),
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Checks if user exists
    try:
        user = User.objects.get(email=serializer.validated_data["email"])
    except User.DoesNotExist:
        return Response(
            USER_NOT_FOUND,
            status=status.HTTP_404_NOT_FOUND,
        )

    # Checks if the user already has the account activated
    if user.is_active == True:
        return Response(
            USER_HAS_ALREADY_ACTIVATED,
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Send code to user email
    try:
        send_activation_code_by_email(serializer.validated_data["email"])
    except smtplib.SMTPException as e:
        return Response(
            __merge_dict(ERROR_SENDING_EMAIL, {"error": str(e)}),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        EMAIL_SEND_TO_USER_SUCCESSFULLY,
        status=status.HTTP_200_OK,
    )


def __merge_dict(original_dict, update_data):
    """
    Creates a deep copy of the original dictionary, updates it with new data, and returns the updated dictionary.

    Args:
        original_dict (dict): The original dictionary to be copied and updated.
        update_data (dict): The dictionary containing data to update the original dictionary with.

    Returns:
        dict: The updated dictionary with new data.
    """
    updated_dict = copy.deepcopy(original_dict)
    updated_dict.update(update_data)
    return updated_dict
