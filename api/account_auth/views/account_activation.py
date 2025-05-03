from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, throttle_classes
from rest_framework.request import Request
from rest_framework.response import Response
from account_auth.constants.http_response import (
    ACCOUNT_HAS_ALREADY_ACTIVATED,
    ACCOUNT_NOT_FOUND,
    ACTIVATED_ACCOUNT,
    CODE_EXPIRED,
    CODE_NOT_FOUND,
    EMAIL_SEND_TO_ACCOUNT_SUCCESSFULLY,
    VALIDATION_ERRORS,
)
from account_auth.documentation_scheme.activate_account import (
    account_not_found_response,
    activate_account_request,
    activated_account_response,
    code_expired_response,
    code_not_found_response,
    email_send_account_response,
    email_validation_errors_and_account_already_activated_response,
)
from account_auth.models import AccountActivationCodeModel, PendingAccountsModel
from account_auth.serializers import EmailSerializer
from account_auth.tasks import (
    task_notify_activated_account,
    task_send_account_activation_code,
)
from account_auth.throttlings import FivePerMinuteRateLimit
from account_auth.utils import deep_merge_dict

Account = get_user_model()


@extend_schema(
    request=EmailSerializer,
    responses={
        200: email_send_account_response,
        400: email_validation_errors_and_account_already_activated_response,
        404: account_not_found_response,
    },
)
@api_view(["POST"])
@throttle_classes([FivePerMinuteRateLimit])
@authentication_classes([])
def request_account_activation_code(request: Request) -> Response:
    """
    Sends an activation code to a registered account who has not yet activated
    their account.

    This view expects a JSON payload containing the account's email.
    If the email belongs to an existing but inactive account, an activation
    code will be sent to their email address.

    A rate limit is applied to prevent excessive requests.

    Authentication:

        - Does not require authentication.
    """
    serializer = EmailSerializer(data=request.data)

    # Check if the provided data is valid.
    if not serializer.is_valid():
        return Response(
            deep_merge_dict(VALIDATION_ERRORS, {"field_errors": serializer.errors}),
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Checks if account exists.
    try:
        account = Account.objects.get(email=serializer.validated_data["email"])
    except Account.DoesNotExist:
        return Response(ACCOUNT_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

    # Checks if the account already has the account activated.
    if account.is_active == True:
        return Response(
            ACCOUNT_HAS_ALREADY_ACTIVATED, status=status.HTTP_400_BAD_REQUEST
        )

    # Send the activation email
    task_send_account_activation_code.delay(serializer.validated_data["email"])

    return Response(EMAIL_SEND_TO_ACCOUNT_SUCCESSFULLY, status=status.HTTP_200_OK)


@extend_schema(
    request=activate_account_request,
    responses={
        200: activated_account_response,
        404: code_not_found_response,
        410: code_expired_response,
    },
)
@api_view(["POST"])
@throttle_classes([FivePerMinuteRateLimit])
@authentication_classes([])
def activate_account(request: Request) -> Response:
    """
    Activates an account based on the provided activation code and applies
    throttle class to limit the rate of activation requests.

    This endpoint allows an account to activate their account by submitting the activation
    code they received via email. The activation code must be valid and not expired.

    Once activated, the account is marked as active in the database. The activation
    code is deleted after successful activation, and the account is notified via email.

    Authentication:

        - Does not require authentication.
    """
    code: str | None = request.data.get("code", None)

    # Checks if code exists in the data base.
    try:
        account_activation_code = AccountActivationCodeModel.objects.get(code=code)
    except AccountActivationCodeModel.DoesNotExist:
        return Response(CODE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

    # Checks if the code is expired.
    now: datetime = timezone.now()
    if account_activation_code.expires_at < now:
        account_activation_code.delete()  # Delete the code as it is no useful.
        return Response(CODE_EXPIRED, status=status.HTTP_410_GONE)

    # Activate account and save in the database.
    account = Account.objects.get(email=account_activation_code.account.email)
    account.is_active = True
    account.save()
    account_activation_code.delete()  # Delete the code as it is no useful.

    # Remove the account from the PendingAccountsModel table after successful activation,
    # since the account is now active and no pending.
    PendingAccountsModel.objects.filter(account=account).delete()

    # Send email to notify activated account.
    task_notify_activated_account.delay(account.email)

    return Response(ACTIVATED_ACCOUNT, status=status.HTTP_200_OK)
