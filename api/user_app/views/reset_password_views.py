from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from user_app.constants.response_codes_and_messages import (
    CODE_EXPIRED,
    CODE_NOT_FOUND,
    EMAIL_SEND_TO_USER_SUCCESSFULLY,
    USER_ACCOUNT_NOT_ACTIVATED,
    USER_NOT_FOUND,
    USER_PASSWORD_RESET,
    VALIDATION_ERRORS,
)
from user_app.models import ResetPasswordCodeModel
from user_app.serializers import EmailSerializer, UserResetPasswordSerializer
from user_app.tasks import task_send_reset_password_code
from user_app.throttlings import FivePerMinuteRateLimit
from user_app.utils.data_utils import merge_dict
from user_app.utils.token_utils import revoke_tokens

User = get_user_model()


@api_view(["POST"])
@throttle_classes([FivePerMinuteRateLimit])
def request_reset_password_code(request):
    """
    Sends a password reset code to the user's registered email address.

    This view expects a JSON payload containing the user's email.
    If the email belongs to an active user, a password reset code will be sent to
    their email. The user can later use this code to reset their forgotten password.
    A rate limit is applied to prevent excessive requests.

    Request Body:
        {
            "email": "user@example.com"
        }
    """
    email_serializer = EmailSerializer(data=request.data)

    if not email_serializer.is_valid():
        return Response(
            merge_dict(VALIDATION_ERRORS, {"field_errors": email_serializer.errors}),
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.get(email=email_serializer.data["email"])
    except User.DoesNotExist:
        return Response(USER_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

    if user.is_active == False:
        return Response(USER_ACCOUNT_NOT_ACTIVATED, status=status.HTTP_403_FORBIDDEN)

    task_send_reset_password_code.delay(email_serializer.data["email"])

    return Response(EMAIL_SEND_TO_USER_SUCCESSFULLY, status=status.HTTP_200_OK)


@api_view(["POST"])
@throttle_classes([FivePerMinuteRateLimit])
def reset_password(request):
    """
    Resets a user's password using a verification code.

    This view receives a password reset code, a new password, and its confirmation.
    It validates if the code exists and is still valid (not expired). If everything
    is correct, the user's password is updated, and the reset code is deleted.
    The user's authentication tokens are also revoked, and a new token pair is returned.

    Request Body:
        {
            "code": "reset_code",
            "new_password": "new_user_password",
            "confirmation_new_password": "new_user_password"
        }
    """
    reset_serializer = UserResetPasswordSerializer(data=request.data)

    if not reset_serializer.is_valid():
        return Response(
            merge_dict(VALIDATION_ERRORS, {"field_errors": reset_serializer.errors}),
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Checks if code exists in the data base
    try:
        reset_password_code = ResetPasswordCodeModel.objects.get(
            code=reset_serializer.data["code"]
        )
    except ResetPasswordCodeModel.DoesNotExist:
        return Response(CODE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

    # Checks if the code is expired
    now: datetime = timezone.now()
    if reset_password_code.expires_at < now:
        reset_password_code.delete()  # Delete the code as it is no longer useful.
        return Response(CODE_EXPIRED, status=status.HTTP_410_GONE)

    # Change use passsoword
    user = User.objects.get(id=reset_password_code.user.id)
    user.set_password(reset_serializer.data["new_password"])
    user.save()

    # Delete the code after use.
    reset_password_code.delete()

    # Revoke all user tokens and return new token pair.
    new_token_pair: dict[str, str] = revoke_tokens(user.id)

    return Response(
        merge_dict(USER_PASSWORD_RESET, new_token_pair), status=status.HTTP_200_OK
    )
