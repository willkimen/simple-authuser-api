import smtplib

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response

from user_app.authentication_classes import JWTAuthentication
from user_app.constants.response_code_messages import (
    ERROR_SENDING_EMAIL,
    USER_REGISTERED_SUCCESSFULLY,
    USER_UPDATED_SUCCESSFULLY,
    VALIDATION_ERRORS,
)
from user_app.serializers import (
    UserRequestSerializer,
    UserResponseSerializer,
    UserUpdateSerializer,
)
from user_app.utils.data_utils import merge_dict
from user_app.utils.email_service import send_activation_code_by_email

User = get_user_model()


@api_view(["POST"])
def register(request):
    """
    Registers a new user in the system.

    This endpoint handles user registration with the following steps:

    1. **Validate Input Data:** The user data is validated using the `UserRequestSerializer`. If the data is invalid, it returns a detailed error response with field-specific validation messages.
    2. **Send Activation Email:** Upon successful validation, an activation email is sent to the provided email address. If there is an issue sending the email, an error response is returned.
    3. **Create User:** If the email is successfully sent, the user is created in the database with the provided data but remains inactive until email activation.
    4. **Return Success Response:** Upon successful registration, a success message along with the user’s data (serialized by `UserResponseSerializer`) is returned.

    Args:
        request (Request): The HTTP request containing the user registration data in JSON format.

    Returns:
        Response: The HTTP response containing either a success message with user data or detailed error messages in case of failure.

    Response Codes:
        - **201 Created:** Registration was successful, and an activation email was sent.
        - **400 Bad Request:** The data provided was invalid. The response contains detailed validation errors for each field.
        - **500 Internal Server Error:** There was an issue sending the activation email.

    Serializers:
        - **UserRequestSerializer:** Used for validating incoming user registration data.
        - **UserResponseSerializer:** Used for serializing the user data upon successful registration.
    """
    request_serializer = UserRequestSerializer(data=request.data)

    # Check if the provided data is valid
    if not request_serializer.is_valid():
        return Response(
            merge_dict(VALIDATION_ERRORS, {"field_errors": request_serializer.errors}),
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Send the activation email
    try:
        send_activation_code_by_email(request_serializer.validated_data["email"])
    except smtplib.SMTPException as e:
        return Response(
            merge_dict(ERROR_SENDING_EMAIL, {"error": str(e)}),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Save the user to the database
    user = request_serializer.save()

    # Serialize the created user data using the response serializer
    response_serializer = UserResponseSerializer(user)

    return Response(
        merge_dict(USER_REGISTERED_SUCCESSFULLY, {"user": response_serializer.data}),
        status=status.HTTP_201_CREATED,
    )


@api_view(["PATCH"])
@authentication_classes([JWTAuthentication])
def update(request):
    """
    Handle partial update of user information for the authenticated user.

    Uses the `UserUpdateSerializer` to validate the provided data and update the user instance.
    If the data is invalid, it returns a detailed error response with field-specific validation errors.
    """

    # Initialize the serializer with the current user instance and the provided data.
    # 'partial=True' allows partial updates (only fields provided in the request will be updated).
    update_serializer = UserUpdateSerializer(
        instance=request.user, data=request.data, partial=True
    )

    # Check if the provided data is valid according to the serializer.
    if not update_serializer.is_valid():
        # If data is invalid, return a response with validation errors.
        return Response(
            merge_dict(VALIDATION_ERRORS, {"field_errors": update_serializer.errors}),
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Save the updated user data to the database.
    user = update_serializer.save()

    # Serialize the updated user data to include in the response.
    response_serializer = UserResponseSerializer(user)

    # Return a success response with the updated user data.
    return Response(
        merge_dict(USER_UPDATED_SUCCESSFULLY, {"user": response_serializer.data}),
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
def user_detail(request):
    """
    Retrieves the details of the authenticated user.

    This endpoint allows an authenticated user to retrieve their own details. It uses the
    `UserResponseSerializer` to serialize the user data and returns it in the response.
    """
    response_serializer = UserResponseSerializer(request.user)
    return Response({"user": response_serializer.data}, status=status.HTTP_200_OK)
