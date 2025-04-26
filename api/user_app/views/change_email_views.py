"""
This module provides views related to user email changes.
"""

from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, throttle_classes
from rest_framework.request import Request
from rest_framework.response import Response
from user_app.authentication.authentication_classes import JWTAuthentication
from user_app.authentication.token_service import revoke_tokens
from user_app.constants.http_response import (
    CODE_EXPIRED,
    CODE_NOT_FOUND,
    EMAIL_ALREADY_EXISTS,
    EMAIL_ALREADY_IN_USE,
    EMAIL_SEND_TO_USER_SUCCESSFULLY,
    USER_EMAIL_CHANGED,
    VALIDATION_ERRORS,
)
from user_app.documentation_scheme.authentication import authentication_errors_response
from user_app.documentation_scheme.change_email import (
    change_email_request,
    code_expired_response,
    code_not_found_response,
    email_already_exists_response,
    email_send_to_user_response,
    email_validation_errors_and_email_already_in_use_response,
    user_email_changed_response,
)
from user_app.models import ChangeEmailCodeModel
from user_app.serializers import EmailSerializer
from user_app.tasks import task_notify_changed_email, task_send_email_change_code
from user_app.throttlings import FivePerMinuteRateLimit
from user_app.utils import deep_merge_dict

User = get_user_model()


@extend_schema(
    request=EmailSerializer,
    responses={
        200: email_send_to_user_response,
        400: email_validation_errors_and_email_already_in_use_response,
        401: authentication_errors_response,
        409: email_already_exists_response,
    },
)
@api_view(["POST"])
@authentication_classes([JWTAuthentication])
def request_email_change_code(request: Request) -> Response:
    """
    Sends a verification code to the new email address provided,
    so that the user can later confirm the email exchange.

    The request should include the new email address they want to switch.

    If the email is valid and not already in use, a verification code will be sent
    to the new email address.

    Authentication:

        - The user must be authenticated using JWT tokens.

        - The token should be provided in the `Authorization` header as a Bearer token.
    """

    # Get email from body request.
    email_serializer = EmailSerializer(data=request.data)

    # Check if the email is normalized.
    if not email_serializer.is_valid():
        return Response(
            deep_merge_dict(
                VALIDATION_ERRORS, {"field_errors": email_serializer.errors}
            ),
            status=status.HTTP_400_BAD_REQUEST,
        )

    new_email: str = email_serializer.data["email"]

    # Checks whether the email received is the same as the authenticated user's,
    # i.e., it is already the email in use.
    if request.user.email == new_email:
        return Response(EMAIL_ALREADY_IN_USE, status=status.HTTP_400_BAD_REQUEST)

    # Checks whether the received email is for another user in the database.
    if User.objects.filter(email=new_email).exists():
        return Response(EMAIL_ALREADY_EXISTS, status=status.HTTP_409_CONFLICT)

    # Send code to user email.
    task_send_email_change_code.delay(request.user.email, new_email)

    return Response(EMAIL_SEND_TO_USER_SUCCESSFULLY, status=status.HTTP_200_OK)


@extend_schema(
    request=change_email_request,
    responses={
        200: user_email_changed_response,
        401: authentication_errors_response,
        404: code_not_found_response,
        410: code_expired_response,
    },
)
@api_view(["POST"])
@throttle_classes([FivePerMinuteRateLimit])
@authentication_classes([JWTAuthentication])
def change_email(request: Request) -> Response:
    """
    Confirms the email change by validating the verification code.

    The user must be logged in and provide the verification code sent
    to their new email address.
    The request should include the verification code.

    If the code is valid and not expired, the user's current email will
    be replaced with the new one.

    After the change, all existing authentication tokens (access and refresh)
    will be blacklisted and returns a new pair of tokens (access and refresh).

    Authentication:

        - The user must be authenticated using JWT tokens.

        - The token should be provided in the `Authorization` header as a Bearer token.
    """
    code: str | None = request.data.get("code", None)

    # Checks if code exists in the data base.
    try:
        change_email_code = ChangeEmailCodeModel.objects.get(code=code)
    except ChangeEmailCodeModel.DoesNotExist:
        return Response(CODE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

    # Checks if the code is expired.
    now: datetime = timezone.now()
    if change_email_code.expires_at < now:
        change_email_code.delete()
        return Response(CODE_EXPIRED, status=status.HTTP_410_GONE)

    # Change email.
    request.user.email = change_email_code.new_email
    request.user.save()
    change_email_code.delete()  # Delete the code as it is no useful.

    # Return new pair tokens.
    token_pair: dict[str, str] = revoke_tokens(request.user.id)

    # Send email to notify changed email.
    task_notify_changed_email.delay(request.user.email)

    return Response(
        deep_merge_dict(USER_EMAIL_CHANGED, token_pair), status=status.HTTP_200_OK
    )
