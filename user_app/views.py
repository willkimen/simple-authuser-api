import os
import smtplib

from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from user_app.serializers import UserSerializer

from .utils.email_service import send_activation_email
from .utils.token import user_active_generate_token

User = get_user_model()


@api_view(["POST"])
def register(request):
    """
    Registers a new user.

    Args:
        request (Request): The request instance containing user data.

    Returns:
        Response: A response containing the registered user data or validation errors.

    This endpoint registers a new user in the system. If the provided data is valid,
    the user is created and an activation email is sent to the provided email address.
    The user is initially marked as inactive until they activate their account through the activation email.
    """
    # Initialize the serializer with the request data
    serializer = UserSerializer(data=request.data)

    # Check if the provided data is valid
    if not serializer.is_valid():
        return Response(
            {"validation_errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )

    # Save the user to the database
    user = serializer.save()
    user.is_active = False  # Mark the user as inactive
    user.save()

    # Send the activation email
    try:
        send_activation_email(user)
    except smtplib.SMTPException as e:
        user.delete()
        return Response(
            {
                "message": "User not created. Error sending email.",
                "error_send_email": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

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


@api_view(["GET"])
def confirmation_register(request, id, token):
    """
    Confirms user registration and activates the account.

    Args:
        request (Request): The request instance.
        id (str): The encoded user ID.
        token (str): The user's activation token.

    Returns:
        HttpResponseRedirect: Redirects to the success or failure URL depending on token validation.

    This function is called when a user clicks on the activation link sent via email.
    It decodes the user ID, checks the existence of the user, and validates the token.
    If the token is valid, the user's account is activated and they are redirected to the success URL.
    Otherwise, the user is redirected to the failure URL.
    """
    # Decode the user ID from the URL-safe base64 string
    id = int(force_str(urlsafe_base64_decode(id)))

    try:
        # Attempt to retrieve the user by ID
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        # Redirect to the failure URL if the user does not exist
        return redirect(os.environ.get("ENV_EMAIL_CONFIRM_FAILURE_URL"))

    # Check if the token is valid
    if user_active_generate_token.check_token(user, token):
        user.is_active = True  # Activate the user's account
        user.save()
        # Redirect to the success URL
        return redirect(os.environ.get("ENV_EMAIL_CONFIRM_SUCCESS_URL"))
    else:
        # Redirect to the failure URL if the token is invalid
        return redirect(os.environ.get("ENV_EMAIL_CONFIRM_FAILURE_URL"))
