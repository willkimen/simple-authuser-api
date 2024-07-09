import smtplib
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response

from .constants import response_messages
from .models import ConfirmationCode
from .serializers import UserSerializer
from .throttlings import ConfirmationRegisterThrottle
from .utils.email_service import send_activation_email

User = get_user_model()


@api_view(["POST"])
def register(request):
    """
    Registers a new user.

    This endpoint registers a new user in the system. If the provided data is valid,
    the user is created and an activation email is sent to the provided email address.
    The user is initially marked as inactive until they activate their account through the activation email.
    """
    serializer = UserSerializer(data=request.data)

    # Check if the provided data is valid
    if not serializer.is_valid():
        return Response(
            {"validation_errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )

    # Send the activation email
    try:
        send_activation_email(serializer.validated_data["email"])
    except smtplib.SMTPException as e:
        return Response(
            {
                "message": response_messages.ERROR_SENDING_EMAIL,
                "error_send_email": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Save the user to the database
    user = serializer.save()
    user.is_active = False  # Mark the user as inactive
    user.save()
    return Response(
        {
            "user": serializer.data,
            "message": response_messages.USER_REGISTERED_SUCCESSFULLY,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["PATCH"])
def update(request, id: int):
    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        return Response(
            {"message": response_messages.USER_NOT_FOUND},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = UserSerializer(instance=user, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(
            {"validation_errors": serializer.errors},
            status=status.status.HTTP_400_BAD_REQUEST,
        )

    serializer.save()
    return Response(
        {
            "user": serializer.data,
            "message": response_messages.USER_UPDATED_SUCCESSFULLY,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@throttle_classes([ConfirmationRegisterThrottle])
def confirmation_register(request):
    """
    Confirms user registration and activates the account.
    """
    code = request.data.get("code", None)

    # Checks if code field was sent by the request
    if code is None:
        return Response(
            {"message": response_messages.CODE_FIELD_IS_REQUIRED},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Convert to string if the type is different
    if not isinstance(code, str):
        code = str(code)

    # Checks if code exists in the data base
    try:
        confirmation_code = ConfirmationCode.objects.get(code=code)
    except ConfirmationCode.DoesNotExist:
        return Response(
            {"message": response_messages.CONFIRMATION_CODE_NOT_FOUND},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Checks if type code is the correct
    if confirmation_code.type_code != "registration_email_confirmation":
        return Response(
            {"message": response_messages.INVALID_CONFIRMATION_CODE_TYPE},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Checks if the code is expired
    expired = timedelta(days=1)
    now = datetime.now()
    if (now - confirmation_code.created_at) >= expired:
        confirmation_code.delete()
        return Response(
            {"message": response_messages.CODE_EXPIRED}, status=status.HTTP_410_GONE
        )

    # Activate user and save in the database
    user = User.objects.get(email=confirmation_code.user_email)
    user.is_active = True
    user.save()
    confirmation_code.delete()
    return Response(
        {"message": response_messages.EMAIL_CONFIRMED}, status=status.HTTP_200_OK
    )
