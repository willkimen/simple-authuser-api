import smtplib

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response

from user_app.constants.response_codes_and_messages import (
    EMAIL_SEND_TO_USER_SUCCESSFULLY,
    ERROR_SENDING_EMAIL,
    USER_ACCOUNT_NOT_ACTIVATED,
    USER_NOT_FOUND,
    VALIDATION_ERRORS,
)
from user_app.serializers import EmailSerializer
from user_app.throttlings import FivePerMinuteRateLimit
from user_app.utils.data_utils import merge_dict
from user_app.utils.email_service import send_reset_password_code_by_email

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
