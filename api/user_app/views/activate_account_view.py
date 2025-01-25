from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from user_app.constants.response_codes_and_messages import (
    ACTIVATED_USER,
    CODE_EXPIRED,
    CODE_NOT_FOUND,
    EMAIL_SEND_TO_USER_SUCCESSFULLY,
    USER_HAS_ALREADY_ACTIVATED,
    USER_NOT_FOUND,
    VALIDATION_ERRORS,
)
from user_app.models import AccountActivationCodeModel
from user_app.serializers import EmailSerializer
from user_app.tasks import task_send_activation_code_by_email
from user_app.throttlings import FivePerMinuteRateLimit
from user_app.utils.data_utils import merge_dict

User = get_user_model()


@api_view(["POST"])
@throttle_classes([FivePerMinuteRateLimit])
def activate_account(request):
    """
    Activates a user account based on the provided activation code and applies
    throttle class to limit the rate of activation requests.
    """
    code = request.data.get("code", None)

    # Checks if code exists in the data base
    try:
        account_activation_code = AccountActivationCodeModel.objects.get(code=code)
    except AccountActivationCodeModel.DoesNotExist:
        return Response(CODE_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

    # Checks if the code is expired
    now: datetime = timezone.now()
    if account_activation_code.expires_at < now:
        account_activation_code.delete()  # Delete the code as it is no longer useful.
        return Response(CODE_EXPIRED, status=status.HTTP_410_GONE)

    # Activate user and save in the database
    user = User.objects.get(email=account_activation_code.user.email)
    user.is_active = True
    user.save()
    account_activation_code.delete()  # Delete the code as it is no longer useful.
    return Response(ACTIVATED_USER, status=status.HTTP_200_OK)


@api_view(["POST"])
@throttle_classes([FivePerMinuteRateLimit])
def send_code_to_activate_account(request):
    """
    Sends an activation email to the user if their account is not already activated and
    throttle class to limit the rate of email requests.
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
        return Response(USER_NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

    # Checks if the user already has the account activated
    if user.is_active == True:
        return Response(USER_HAS_ALREADY_ACTIVATED, status=status.HTTP_400_BAD_REQUEST)

    # Send the activation email
    task_send_activation_code_by_email.delay(serializer.validated_data["email"])

    return Response(EMAIL_SEND_TO_USER_SUCCESSFULLY, status=status.HTTP_200_OK)
