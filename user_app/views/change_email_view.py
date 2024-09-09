import smtplib

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, throttle_classes
from rest_framework.response import Response

from user_app.authentication_classes import JWTAuthentication
from user_app.constants.response_code_messages import (
    EMAIL_ALREADY_EXISTS,
    EMAIL_ALREADY_IN_USE,
    EMAIL_SEND_TO_USER_SUCCESSFULLY,
    ERROR_SENDING_EMAIL,
)
from user_app.utils.data_utils import merge_dict
from user_app.utils.email_service import send_change_email_code_by_email

User = get_user_model()


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
def send_code_to_email_change(request):
    new_email = request.POST.get("new_email", None)

    if request.user.email == new_email:
        return Response(EMAIL_ALREADY_IN_USE, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=new_email).exists():
        return Response(EMAIL_ALREADY_EXISTS, status=status.HTTP_409_CONFLICT)

    try:
        send_change_email_code_by_email(request.user.email, new_email)
    except smtplib.SMTPException as e:
        return Response(
            merge_dict(ERROR_SENDING_EMAIL, {"error": str(e)}),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(EMAIL_SEND_TO_USER_SUCCESSFULLY, status=status.HTTP_200_OK)
