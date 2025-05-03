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
    ACCOUNT_NOT_ACTIVATED,
    ACCOUNT_NOT_FOUND,
    ACCOUNT_PASSWORD_RESET,
    CODE_EXPIRED,
    CODE_NOT_FOUND,
    EMAIL_SEND_TO_ACCOUNT_SUCCESSFULLY,
    VALIDATION_ERRORS,
)
from user_app.documentation_scheme.reset_password import (
    account_not_activated_response,
    account_not_found_response,
    account_password_reset_response,
    code_expired_response,
    code_not_found_response,
    email_send_to_account_response,
    email_validation_errors_response,
    passwords_validation_errors_response,
)
from user_app.models import ResetPasswordCodeModel
from user_app.serializers import AccountResetPasswordSerializer, EmailSerializer
from user_app.tasks import task_notify_reset_password, task_send_reset_password_code
from user_app.throttlings import FivePerMinuteRateLimit
from user_app.utils import deep_merge_dict

Account = get_user_model()


@extend_schema(
    request=EmailSerializer,
    responses={
        200: email_send_to_account_response,
        400: email_validation_errors_response,
        403: account_not_activated_response,
        404: account_not_found_response,
    },
)
@api_view(["POST"])
@throttle_classes([FivePerMinuteRateLimit])
@authentication_classes([])
def request_reset_password_code(request: Request) -> Response:
    """
    Sends a password reset code to the account's email address.

    This view expects a JSON containing the account's email.

    If the email belongs to an active account, a password reset code will be sent to
    their email. The account can later use this code to reset their forgotten password.

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

    # Verify if account exists.
    try:
        account = Account.objects.get(email=email_serializer.data["email"])
    except Account.DoesNotExist:
        return Response(ACCOUNT_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

    # Verify if account is active or not.
    if account.is_active == False:
        return Response(ACCOUNT_NOT_ACTIVATED, status=status.HTTP_403_FORBIDDEN)

    # Send code to account email address.
    task_send_reset_password_code.delay(email_serializer.data["email"])

    return Response(EMAIL_SEND_TO_ACCOUNT_SUCCESSFULLY, status=status.HTTP_200_OK)


@extend_schema(
    request=AccountResetPasswordSerializer,
    responses={
        201: account_password_reset_response,
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
    Resets an account's password using a verification code.

    This view receives a password reset code, a new password and its confirmation.

    It validates if the code exists and is still valid (not expired). If everything
    is correct, the account's password is updated, and the reset code is deleted.

    The account's authentication tokens are also revoked, and a new token pair is returned.

    Authentication:

        - Does not require authentication.
    """
    reset_serializer = AccountResetPasswordSerializer(data=request.data)

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
    account = Account.objects.get(id=reset_password_code.account.id)
    account.set_password(reset_serializer.data["new_password"])
    account.save()

    # Delete the code after use.
    reset_password_code.delete()

    # Revoke all account tokens and return new token pair.
    new_token_pair: dict[str, str] = revoke_tokens(account.id)

    # Send email to notify reset password.
    task_notify_reset_password.delay(account.email)

    return Response(
        deep_merge_dict(ACCOUNT_PASSWORD_RESET, new_token_pair),
        status=status.HTTP_200_OK,
    )
