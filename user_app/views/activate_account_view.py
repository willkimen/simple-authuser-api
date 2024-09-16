import smtplib
from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils.timezone import make_aware
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response

from user_app.constants.response_code_messages import (
    CODE_EXPIRED,
    CODE_FIELD_IS_REQUIRED,
    CODE_NOT_FOUND,
    EMAIL_SEND_TO_USER_SUCCESSFULLY,
    ERROR_SENDING_EMAIL,
    USER_ACTIVATED,
    USER_HAS_ALREADY_ACTIVATED,
    USER_NOT_FOUND,
    VALIDATION_ERRORS,
)
from user_app.models import AccountActivationCodeModel
from user_app.serializers import EmailSerializer
from user_app.throttlings import FivePerMinuteRateLimit
from user_app.utils.data_utils import merge_dict
from user_app.utils.email_service import send_activation_code_by_email

User = get_user_model()


@api_view(["POST"])
@throttle_classes([FivePerMinuteRateLimit])
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
        - 404 Not Found: The provided activation code does not exist in the database.
        - 410 Gone: The provided activation code has expired.

    Throttling:
        - Applies FivePerMinuteRateLimit throttle class to limit the rate of activation requests.
    """
    code = request.data.get("code", None)

    # Checks if code field was sent by the request
    if code is None:
        return Response(
            CODE_FIELD_IS_REQUIRED,
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Checks if code exists in the data base
    try:
        account_activation_code = AccountActivationCodeModel.objects.get(code=code)
    except AccountActivationCodeModel.DoesNotExist:
        return Response(
            CODE_NOT_FOUND,
            status=status.HTTP_404_NOT_FOUND,
        )

    # Checks if the code is expired
    now = make_aware(datetime.now())
    if account_activation_code.expires_at < now:
        account_activation_code.delete()
        return Response(
            CODE_EXPIRED,
            status=status.HTTP_410_GONE,
        )

    # Activate user and save in the database
    user = User.objects.get(email=account_activation_code.user.email)
    user.is_active = True
    user.save()
    account_activation_code.delete()
    return Response(USER_ACTIVATED, status=status.HTTP_200_OK)


@api_view(["POST"])
@throttle_classes([FivePerMinuteRateLimit])
def send_code_to_activate_account(request):
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
        - Applies FivePerMinuteRateLimit throttle class to limit the rate of email requests.
    """
    serializer = EmailSerializer(data=request.data)

    # Check if the provided data is valid
    if not serializer.is_valid():
        return Response(
            merge_dict(VALIDATION_ERRORS, {"field_errors": serializer.errors}),
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
            merge_dict(ERROR_SENDING_EMAIL, {"error": str(e)}),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        EMAIL_SEND_TO_USER_SUCCESSFULLY,
        status=status.HTTP_200_OK,
    )
