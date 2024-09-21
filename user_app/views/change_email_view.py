"""
This module provides views related to user email changes.
"""

import smtplib

from django.contrib.auth import get_user_model
from django.utils import timezone
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
    Sends a code to change the email address to the authenticated user.
    """

    # Get email from body request.
    email_serializer = EmailSerializer(data=request.data)

    # Check if the email is normalized.
    if not email_serializer.is_valid():
        return Response(
            merge_dict(VALIDATION_ERRORS, {"field_errors": email_serializer.errors}),
            status=status.HTTP_400_BAD_REQUEST,
        )

    new_email = email_serializer.data["email"]

    # Checks whether the email received is the same as the authenticated user's,
    # i.e., it is already the email in use.
    if request.user.email == new_email:
        return Response(EMAIL_ALREADY_IN_USE, status=status.HTTP_400_BAD_REQUEST)

    # Checks whether the received email is for another user in the database.
    if User.objects.filter(email=new_email).exists():
        return Response(EMAIL_ALREADY_EXISTS, status=status.HTTP_409_CONFLICT)

    # Try sending an email.
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
@authentication_classes([JWTAuthentication])
def change_user_email(request):
    """
    This view waits to receive the code and exchanges the user's email.
    """
    code = request.data.get("code", None)

    # Checks if code exists in the data base
    try:
        change_email_code = ChangeEmailCodeModel.objects.get(code=code)
    except ChangeEmailCodeModel.DoesNotExist:
        return Response(CODE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

    # Checks if the code is expired
    now = timezone.now()
    if change_email_code.expires_at < now:
        change_email_code.delete()
        return Response(
            CODE_EXPIRED,
            status=status.HTTP_410_GONE,
        )

    # Change email
    request.user.email = change_email_code.new_email
    request.user.save()
    change_email_code.delete()  # Delete the code as it is no longer useful.

    return Response(USER_EMAIL_CHANGED, status=status.HTTP_200_OK)
