"""
This module provides views related to user email changes.
"""

from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, throttle_classes
from rest_framework.response import Response
from user_app.authentication_classes import JWTAuthentication
from user_app.constants.response_codes_and_messages import (
    CODE_EXPIRED,
    CODE_NOT_FOUND,
    EMAIL_ALREADY_EXISTS,
    EMAIL_ALREADY_IN_USE,
    EMAIL_SEND_TO_USER_SUCCESSFULLY,
    USER_EMAIL_CHANGED,
    VALIDATION_ERRORS,
)
from user_app.models import ChangeEmailCodeModel
from user_app.serializers import EmailSerializer
from user_app.tasks import task_send_email_change_code
from user_app.throttlings import FivePerMinuteRateLimit
from user_app.utils.data_utils import merge_dict
from user_app.utils.token_utils import revoke_tokens

User = get_user_model()


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
def request_email_change_code(request):
    """
    Sends a verification code to the new email address provided by the
    authenticated user.

    The user must be logged in to request a code to change their email address.
    The request should include the new email address they want to switch to in
    JSON format:

    Example request body:
    {
        "email": "newemail@example.com"
    }

    If the email is valid and not already in use, a verification code will be sent
    to the new email address.
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

    # Send code to user email
    task_send_email_change_code.delay(request.user.email, new_email)

    return Response(EMAIL_SEND_TO_USER_SUCCESSFULLY, status=status.HTTP_200_OK)


@api_view(["POST"])
@throttle_classes([FivePerMinuteRateLimit])
@authentication_classes([JWTAuthentication])
def change_email(request):
    """
    Confirms the email change by validating the verification code.

    The user must be logged in and provide the verification code sent
    to their new email address.
    The request should include the verification code in JSON format:

    Example request body:
    {
        "code": "chg-code"
    }

    If the code is valid and not expired, the user's current email will
    be replaced with the new one.

    After the change, all existing authentication tokens (access and refresh)
    will be blacklisted, requiring the user to log in again using the new email.
    """
    code = request.data.get("code", None)

    # Checks if code exists in the data base
    try:
        change_email_code = ChangeEmailCodeModel.objects.get(code=code)
    except ChangeEmailCodeModel.DoesNotExist:
        return Response(CODE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

    # Checks if the code is expired
    now: datetime = timezone.now()
    if change_email_code.expires_at < now:
        change_email_code.delete()
        return Response(CODE_EXPIRED, status=status.HTTP_410_GONE)

    # Change email
    request.user.email = change_email_code.new_email
    request.user.save()
    change_email_code.delete()  # Delete the code as it is no longer useful.

    token_pair: dict[str, str] = revoke_tokens(request.user.id)

    return Response(
        merge_dict(USER_EMAIL_CHANGED, token_pair), status=status.HTTP_200_OK
    )
