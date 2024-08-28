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
    IS_NOT_ACCESS_OR_REFRESH_TOKEN,
    IS_NOT_REFRESH_TOKEN,
    JWT_ACCESS_CREATED,
    LOGIN_SUCCESSFUL,
    LOGOUT_SUCCESSFUL,
    USER_ACCOUNT_NOT_ACTIVATED,
    USER_ACTIVATED,
    USER_HAS_ALREADY_ACTIVATED,
    USER_NOT_FOUND,
    USER_REGISTERED_SUCCESSFULLY,
    USER_TOKEN_MISMATCH,
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
    Registers a new user in the system.

    This endpoint handles user registration. It performs the following steps:
    1. **Validate Input Data:** Uses the `UserSerializer` to validate the provided user data. If the data is invalid, it returns a detailed validation error response.
    2. **Send Activation Email:** Attempts to send an activation email to the provided email address. If email sending fails, it returns an error response.
    3. **Save User:** If the data is valid and the email is successfully sent, the user is created in the database with an inactive status.
    4. **Return Success Response:** Returns a success message along with the user data if the registration is successful.

    Args:
        request (Request): The HTTP request object containing user registration data.

    Returns:
        Response: The HTTP response object containing either a success message or error details.

    Response Codes:
        - 201 Created: Successfully registered the user and sent an activation email.
        - 400 Bad Request: The provided data is invalid, with detailed field errors.
        - 500 Internal Server Error: Failed to send the activation email.
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
        __merge_dict(JWT_ACCESS_CREATED, {"access": create_access_jwt(payload["uid"])}),
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
    JWTBlackList.objects.create(
        jti=payload["jti"],
        exp=payload["exp"],
        typ=payload["typ"],
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
    Activates a user account based on the provided activation code.

    This endpoint verifies the activation code provided by the user and activates their account if the code is valid.
    The code must be of the correct type, not expired, and present in the database. Upon successful activation,
    the user's account is updated to active status, and the activation code is deleted.

    Args:
        request (Request): The HTTP request object containing the activation code.

    Returns:
        Response: An HTTP response object indicating the result of the activation process.

    Response Codes:
        - 200 OK: The user account was successfully activated.
        - 400 Bad Request: The provided code field is missing or the code type is invalid.
        - 404 Not Found: The provided activation code does not exist in the database.
        - 410 Gone: The provided activation code has expired.

    Throttling:
        - Applies `AccountActivationRequestRateLimit` throttle class to limit the rate of activation requests.
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
    """
    Sends an activation email to the user if their account is not already activated.

    This endpoint handles the process of sending an activation email to the user. It first validates the provided
    email address and checks whether the user exists and if their account is already activated. If the user is valid
    and their account is not activated, an activation code is sent to their email address.

    Args:
        request (Request): The HTTP request object containing the email address.

    Returns:
        Response: An HTTP response object indicating the result of the email sending process.

    Response Codes:
        - 200 OK: The activation email was successfully sent to the user.
        - 400 Bad Request: The user account is already activated, or the provided data is invalid.
        - 404 Not Found: The user with the provided email does not exist.
        - 500 Internal Server Error: An error occurred while sending the activation email.

    Throttling:
        - Applies `SendEmailActivateAccountRequestRateLimit` throttle class to limit the rate of email requests.
    """
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
