from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers

# Get the custom user model
User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for registering new users. Validates and creates a new user in the system.
    """

    # Additional field to confirm the password, should always be write_only
    confirmation_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "id",
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

        Raises:
            serializers.ValidationError: If the passwords do not match.

        Returns:
            dict: Validated data.
        """
        # Check if the password and confirmation_password match
        if data.get("password") != data.get("confirmation_password"):
            raise serializers.ValidationError(
                detail={"confirmation_password": "Passwords do not match"}
            )
        return data

    def validate_password(self, password):
        """
        Validates the password strength using Django's standard validations.

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
