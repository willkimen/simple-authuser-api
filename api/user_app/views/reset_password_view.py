import smtplib
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
    ERROR_SENDING_EMAIL,
    USER_ACCOUNT_NOT_ACTIVATED,
    USER_NOT_FOUND,
    USER_PASSWORD_RESET,
    VALIDATION_ERRORS,
)
from user_app.models import ResetPasswordCodeModel
from user_app.serializers import EmailSerializer, UserResetPasswordSerializer
from user_app.throttlings import FivePerMinuteRateLimit
from user_app.utils.data_utils import merge_dict
from user_app.utils.email_service import send_reset_password_code_by_email
from user_app.utils.token_utils import revoke_tokens

User = get_user_model()


@api_view(["POST"])
@throttle_classes([FivePerMinuteRateLimit])
def send_code_to_reset_password(request):
    """
    This view handles the request to send a password reset code to the
    user's email address.

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

    # Try sending an email.
    try:
        send_reset_password_code_by_email(email_serializer.data["email"])
    except smtplib.SMTPException as e:
        return Response(
            merge_dict(ERROR_SENDING_EMAIL, {"error": str(e)}),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(EMAIL_SEND_TO_USER_SUCCESSFULLY, status=status.HTTP_200_OK)


@api_view(["POST"])
@throttle_classes([FivePerMinuteRateLimit])
def reset_password(request):
    """
    View for resetting a user's password.

    This view receives a reset code and a new password, validates if the code exists,
    if it's still valid (not expired), and on success, resets the user's password.

    Parameters:
    - code (str): Password reset code sent via email.
    - new_password (str): The new password desired by the user.
    - confirmation_new_password (str): The password for confirmation.
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
