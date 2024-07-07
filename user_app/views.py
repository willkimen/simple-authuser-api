import smtplib
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import ConfirmationCode
from .serializers import UserSerializer
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
                "message": "User not created. Error sending email.",
                "error_send_email": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Save the user to the database
    user = serializer.save()
    user.is_active = False  # Mark the user as inactive
    user.save()
    return Response(
        {"user": serializer.data, "message": "User registered successfully"},
        status=status.HTTP_201_CREATED,
    )


@api_view(["PATCH"])
def update(request, id: int):
    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        return Response(
            {"message": "User with id not found."}, status=status.HTTP_400_BAD_REQUEST
        )

    serializer = UserSerializer(instance=user, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(
            {"validation_errors": serializer.errors},
            status=status.status.HTTP_400_BAD_REQUEST,
        )

    serializer.save()
    return Response(
        {"user": serializer.data, "message": "User updated successfully."},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def confirmation_register(request):
    """
    Confirms user registration and activates the account.
    """
    code = request.POST.get("code")

    # Checks if code exists in the data base
    try:
        confirmation_code = ConfirmationCode.objects.get(code=code)
    except ConfirmationCode.DoesNotExist:
        return Response(
            {"message": "Confirmation code not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Checks if user has already activate
    user = User.objects.get(email=confirmation_code.user_email)
    if user.is_active == True:
        return Response(
            {"message": "User has already confirmed email"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Checks if type code is the correct
    if confirmation_code.type_code != "registration_email_confirmation":
        return Response(
            {
                "message": "Invalid confirmation code type. The code does not belong to the email confirmation type"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Checks if the code is expired
    expired = timedelta(days=1)
    now = datetime.now()
    if (now - confirmation_code.created_at) >= expired:
        confirmation_code.delete()
        return Response({"message": "Code expired"}, status=status.HTTP_410_GONE)

    # Activate user and save in the database
    user.is_active = True
    user.save()
    return Response(
        {"message": "User email confirmed successfully"}, status=status.HTTP_200_OK
    )
