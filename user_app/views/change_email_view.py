import smtplib
from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils.timezone import make_aware
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, throttle_classes
from rest_framework.response import Response

from user_app.authentication_classes import JWTAuthentication
from user_app.constants.response_code_messages import (
    CODE_EXPIRED,
    CODE_NOT_FOUND,
    EMAIL_ALREADY_EXISTS,
    EMAIL_ALREADY_IN_USE,
    EMAIL_SEND_TO_USER_SUCCESSFULLY,
    ERROR_SENDING_EMAIL,
    USER_EMAIL_CHANGED,
    USER_NOT_FOUND,
    VALIDATION_ERRORS,
)
from user_app.models import ChangeEmailCodeModel
from user_app.serializers import EmailSerializer
from user_app.throttlings import FivePerMinuteRateLimit
from user_app.utils.data_utils import merge_dict
from user_app.utils.email_service import send_change_email_code_by_email

User = get_user_model()


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
def send_code_to_email_change(request):
    """
    Handles the process of sending a confirmation code to the user's new email address for email change.

    This view checks if the new email is already in use or exists in the system. If the email is valid and not already in use, it generates a confirmation code and sends it to the new email.

    The function uses JWT authentication to verify the user's identity.

    Args:
        request (HttpRequest): The request object containing the user's authentication and the new email address.

    Request Data:
        - `email` (str): The new email address to which the confirmation code will be sent.

    Returns:
        Response:
            - 400 Bad Request: If the new email is the same as the current user's email.
            - 409 Conflict: If the new email already exists in the system.
            - 500 Internal Server Error: If there's an error while sending the email.
            - 200 OK: If the confirmation code is successfully sent to the new email.
    """

    email_serializer = EmailSerializer(data=request.data)
    if not email_serializer.is_valid():
        return Response(
            merge_dict(VALIDATION_ERRORS, {"field_errors": email_serializer.errors}),
            status=status.HTTP_400_BAD_REQUEST,
        )

    new_email = email_serializer.data["email"]

    if request.user.email == new_email:
        return Response(EMAIL_ALREADY_IN_USE, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=new_email).exists():
        return Response(EMAIL_ALREADY_EXISTS, status=status.HTTP_409_CONFLICT)
    try:
        send_change_email_code_by_email(request.user.email, new_email)
    except smtplib.SMTPException as e:
        return Response(
            merge_dict(ERROR_SENDING_EMAIL, {"error": str(e)}),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(EMAIL_SEND_TO_USER_SUCCESSFULLY, status=status.HTTP_200_OK)


@api_view(["POST"])
@throttle_classes([FivePerMinuteRateLimit])
def change_user_email(request):
    """
    Handles the process of changing the user's email after verifying the confirmation code.

    This view verifies if the provided confirmation code exists in the database and is not expired. If valid, it updates the user's email with the new one stored in the code entry.

    Args:
        request (HttpRequest): The request object containing the confirmation code.

    Request Data:
        - `code` (str): The confirmation code provided by the user for email change.

    Returns:
        Response:
            - 404 Not Found:
                - If the provided code does not exist in the system.
                - If the user associated with the actual email is not found.
            - 410 Gone: If the confirmation code has expired.
            - 200 OK: If the email is successfully changed.
    """
    code = request.data.get("code", None)

    # Checks if code exists in the data base
    try:
        change_email_code = ChangeEmailCodeModel.objects.get(code=code)
    except ChangeEmailCodeModel.DoesNotExist:
        return Response(CODE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

    # Checks if the code is expired
    now = make_aware(datetime.now())
    if change_email_code.expires_at < now:
        change_email_code.delete()
        return Response(
            CODE_EXPIRED,
            status=status.HTTP_410_GONE,
        )

    try:
        user = User.objects.get(email=change_email_code.actual_email)
    except User.DoesNotExist:
        return Response(
            USER_NOT_FOUND,
            status=status.HTTP_404_NOT_FOUND,
        )

    user.email = change_email_code.new_email
    user.save()
    change_email_code.delete()

    return Response(USER_EMAIL_CHANGED, status=status.HTTP_200_OK)
