from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, throttle_classes
from rest_framework.request import Request
from rest_framework.response import Response
from user_app.authentication.token_service import revoke_tokens
from user_app.constants.http_response import (
    CODE_EXPIRED,
    CODE_NOT_FOUND,
    EMAIL_SEND_TO_USER_SUCCESSFULLY,
    USER_ACCOUNT_NOT_ACTIVATED,
    USER_NOT_FOUND,
    USER_PASSWORD_RESET,
    VALIDATION_ERRORS,
)
from user_app.documentation_scheme.reset_password import (
    code_expired_response,
    code_not_found_response,
    email_send_to_user_response,
    email_validation_errors_response,
    passwords_validation_errors_response,
    user_account_not_activated_response,
    user_not_found_response,
    user_password_reset_response,
)
from user_app.models import ResetPasswordCodeModel
from user_app.serializers import EmailSerializer, UserResetPasswordSerializer
from user_app.tasks import task_notify_reset_password, task_send_reset_password_code
from user_app.throttlings import FivePerMinuteRateLimit
from user_app.utils import deep_merge_dict

User = get_user_model()


@extend_schema(
    request=EmailSerializer,
    responses={
        200: email_send_to_user_response,
        400: email_validation_errors_response,
        403: user_account_not_activated_response,
        404: user_not_found_response,
    },
)
@api_view(["POST"])
@throttle_classes([FivePerMinuteRateLimit])
@authentication_classes([])
def request_reset_password_code(request: Request) -> Response:
    """
    Sends a password reset code to the user's email address.

    This view expects a JSON containing the user's email.

    If the email belongs to an active user, a password reset code will be sent to
    their email. The user can later use this code to reset their forgotten password.

    A rate limit is applied to prevent excessive requests.

    Authentication:

        - Does not require authentication.
    """
    email_serializer = EmailSerializer(data=request.data)

    # Check if the provided data is valid according to the serializer.
    if not email_serializer.is_valid():
        return Response(
            deep_merge_dict(
                VALIDATION_ERRORS, {"field_errors": email_serializer.errors}
            ),
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Verify if user exists.
    try:
        user = User.objects.get(email=email_serializer.data["email"])
    except User.DoesNotExist:
        return Response(USER_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

    # Verify if user is active or not.
    if user.is_active == False:
        return Response(USER_ACCOUNT_NOT_ACTIVATED, status=status.HTTP_403_FORBIDDEN)

    # Send code to user email address.
    task_send_reset_password_code.delay(email_serializer.data["email"])

    return Response(EMAIL_SEND_TO_USER_SUCCESSFULLY, status=status.HTTP_200_OK)


@extend_schema(
    request=UserResetPasswordSerializer,
    responses={
        201: user_password_reset_response,
        400: passwords_validation_errors_response,
        404: code_not_found_response,
        410: code_expired_response,
    },
)
@api_view(["POST"])
@throttle_classes([FivePerMinuteRateLimit])
@authentication_classes([])
def reset_password(request: Request) -> Response:
    """
    Resets a user's password using a verification code.

    This view receives a password reset code, a new password and its confirmation.

    It validates if the code exists and is still valid (not expired). If everything
    is correct, the user's password is updated, and the reset code is deleted.

    The user's authentication tokens are also revoked, and a new token pair is returned.

    Authentication:

        - Does not require authentication.
    """
    reset_serializer = UserResetPasswordSerializer(data=request.data)

    # Check if the provided data is valid according to the serializer.
    if not reset_serializer.is_valid():
        return Response(
            deep_merge_dict(
                VALIDATION_ERRORS, {"field_errors": reset_serializer.errors}
            ),
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Checks if code exists in the data base.
    try:
        reset_password_code = ResetPasswordCodeModel.objects.get(
            code=reset_serializer.data["code"]
        )
    except ResetPasswordCodeModel.DoesNotExist:
        return Response(CODE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

    # Checks if the code is expired.
    now: datetime = timezone.now()
    if reset_password_code.expires_at < now:
        reset_password_code.delete()  # Delete the code as it is no useful.
        return Response(CODE_EXPIRED, status=status.HTTP_410_GONE)

    # Change use password.
    user = User.objects.get(id=reset_password_code.user.id)
    user.set_password(reset_serializer.data["new_password"])
    user.save()

    # Delete the code after use.
    reset_password_code.delete()

    # Revoke all user tokens and return new token pair.
    new_token_pair: dict[str, str] = revoke_tokens(user.id)

    # Send email to notify reset password.
    task_notify_reset_password.delay(user.email)

    return Response(
        deep_merge_dict(USER_PASSWORD_RESET, new_token_pair), status=status.HTTP_200_OK
    )
