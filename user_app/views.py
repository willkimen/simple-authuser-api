from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from user_app.serializers import UserSerializer

from .utils.email_service import send_activation_email

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
    send_activation_email(user, request)

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


# TODO nao finalizado
def confirmation_register(request, id, token): ...
