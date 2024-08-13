import smtplib
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.utils.timezone import make_aware
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, throttle_classes
from rest_framework.response import Response

from user_app.authentication_classes import JWTAuthentication
from user_app.constants import confirmation_type_code, response_messages
from user_app.models import ConfirmationCode, JWTBlackList
from user_app.serializers import EmailSerializer, UserSerializer
from user_app.throttlings import (
    AccountActivationRequestRateLimit,
    SendEmailActivateAccountRequestRateLimit,
)
from user_app.utils.email_service import send_activation_code_by_email
from user_app.utils.jwt_token import create_pair_jwt

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
        send_activation_code_by_email(serializer.validated_data["email"])
    except smtplib.SMTPException as e:
        return Response(
            {
                "message": response_messages.ERROR_SENDING_EMAIL,
                "error_send_email": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Save the user to the database
    serializer.save()
    return Response(
        {
            "user": serializer.data,
            "message": response_messages.USER_REGISTERED_SUCCESSFULLY,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
def login(request):
    """
    Handle user login by email and password.

    Args:
        request (Request): The request object containing email and password.

    Returns:
        Response: A response object containing JWT tokens if successful or an error message if failed.
    """
    email = request.data.get("email", None)
    password = request.data.get("password", None)

    # Verify if user exists
    try:
        user = User.objects.get(email=email, password=password)
    except User.DoesNotExist:
        return Response(
            {"message": response_messages.USER_NOT_FOUND},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Verify if user has activated account
    if user.is_active is False:
        return Response(
            {"message": response_messages.USER_ACCOUNT_NOT_ACTIVATED},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Create pair jwt: access and refresh
    pair_jwt: dict[str:str] = create_pair_jwt(user.id)

    return Response(pair_jwt, status=status.HTTP_200_OK)


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
def logout(request):
    JWTBlackList.objects.create(
        jti=request.auth["jti"],
        exp=request.auth["exp"],
        typ=request.auth["typ"],
    )

    return Response(
        {"message": response_messages.LOGOUT_SUCCESSFUL}, status=status.HTTP_200_OK
    )


@api_view(["PATCH"])
def update(request, id: int):
    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        return Response(
            {"message": response_messages.USER_NOT_FOUND},
            status=status.HTTP_404_NOT_FOUND,
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
@throttle_classes([AccountActivationRequestRateLimit])
def activate_account(request):
    """
    Verify code and activates the user account.
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
            {"message": response_messages.ACCOUNT_ACTIVATION_CODE_NOT_FOUND},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Checks if type code is the correct
    if confirmation_code.type_code != confirmation_type_code.ACCOUNT_ACTIVATION:
        return Response(
            {"message": response_messages.INVALID_CONFIRMATION_CODE_TYPE},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Checks if the code is expired
    expired = timedelta(days=1)
    now = make_aware(datetime.now())
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
        {"message": response_messages.ACCOUNT_ACTIVATED}, status=status.HTTP_200_OK
    )


@api_view(["POST"])
@throttle_classes([SendEmailActivateAccountRequestRateLimit])
def send_email_to_activate_account(request):
    serializer = EmailSerializer(data=request.data)

    # Check if the provided data is valid
    if not serializer.is_valid():
        return Response(
            {"validation_errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )

    # Checks if user exists
    try:
        user = User.objects.get(email=serializer.validated_data["email"])
    except User.DoesNotExist:
        return Response(
            {"message": response_messages.USER_NOT_FOUND},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Checks if the user already has the account activated
    if user.is_active == True:
        return Response(
            {"message": response_messages.USER_HAS_ALREADY_ACTIVATED},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Send email
    try:
        send_activation_code_by_email(serializer.validated_data["email"])
    except smtplib.SMTPException as e:
        return Response(
            {
                "message": response_messages.ERROR_SENDING_EMAIL,
                "error_send_email": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        {"message": response_messages.EMAIL_SEND_TO_USER_SUCCESSFULLY},
        status=status.HTTP_200_OK,
    )
