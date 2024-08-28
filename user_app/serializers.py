from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers

from user_app.constants import validation_error_messages

# Get the custom user model
User = get_user_model()


class UserRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for registering new users. Validates and creates a new user in the system.

    Attributes:
        confirmation_password (CharField): Additional field to confirm the password.
    """

    # Additional field to confirm the password, should always be write_only
    confirmation_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "password",
            "confirmation_password",
        ]
        # Set fields as write_only so they are not displayed in responses
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        """
        Creates and returns a new user after validating the data.

        Args:
            validated_data (dict): Validated data of the new user.

        Returns:
            UserProfile: The created user.
        """
        # Remove the confirmation_password field from the validated data
        validated_data.pop("confirmation_password", None)
        # Create the user with the provided data
        return User.objects.create_user(**validated_data)

    def validate(self, data):
        """
        Validates the data provided during registration.

        Args:
            data (dict): Data to be validated.

        Raises:
            serializers.ValidationError: If the passwords do not match.

        Returns:
            dict: Validated data.
        """
        # Check if the password and confirmation_password match
        if data.get("password") != data.get("confirmation_password"):
            raise serializers.ValidationError(
                detail={
                    "confirmation_password": validation_error_messages.PASSWORD_DO_NOT_MATCH
                }
            )
        return data

    def validate_password(self, password):
        """
        Validates the password strength using Django's standard validations.

        Args:
            password (str): The password to be validated.

        Raises:
            serializers.ValidationError: If the password does not meet the validation requirements.

        Returns:
            str: The validated password.
        """
        try:
            # Use Django's standard password validation
            validate_password(password)
        except ValidationError as e:
            # Raise a validation error with the details of the error
            raise serializers.ValidationError(detail=e)
        return password


class UserResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for returning user data in the response.

    This serializer is used for formatting the user data in the response
    after a successful registration. It excludes sensitive fields like the password.
    """

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "is_active"]


class EmailSerializer(serializers.Serializer):
    """
    Serializer for handling email input.
    """

    email = serializers.EmailField()
