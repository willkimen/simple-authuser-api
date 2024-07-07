import pytest
from django.contrib.auth import get_user_model  # type: ignore
from rest_framework.exceptions import ErrorDetail  # type: ignore

from user_app.serializers import UserSerializer

User = get_user_model()


# Fixtures to provide test data
@pytest.fixture
def user_with_valid_fields():
    """
    Returns valid data for a new user.
    """
    return {
        "email": "user@email.com",
        "password": "1234_!pass",
        "confirmation_password": "1234_!pass",
        "first_name": "my_name",
        "last_name": "my_last_name",
    }


@pytest.fixture
def user_with_differents_passwords():
    """
    Returns user data where the passwords do not match.
    """
    return {
        "email": "user@email.com",
        "password": "1234_!pass",
        "confirmation_password": "1234_!pass_unmatched",
        "first_name": "my_name",
        "last_name": "my_last_name",
    }


@pytest.fixture
def user_with_invalid_passwords():
    """
    Returns user data with an invalid password.
    """
    return {
        "email": "user@email.com",
        "password": "1234",
        "confirmation_password": "1234",
        "first_name": "my_name",
        "last_name": "my_last_name",
    }


@pytest.mark.django_db
def test_invalid_when_passwords_differ(user_with_differents_passwords: dict):
    """
    Tests if an error is raised when the passwords do not match.
    """
    expected_error_message = "Passwords do not match"

    # Initialize the serializer with the user data
    serializer = UserSerializer(data=user_with_differents_passwords)

    # Check if the serializer is invalid and the error message is as expected
    assert (
        not serializer.is_valid()
    ), "Serializer should be invalid when the passwords do not match."

    # Get the ErrorDetail object containing the error message for the confirmation_password field
    error_detail_field: ErrorDetail = serializer.errors.get(
        "confirmation_password", []
    )[0]

    # Get the message from the ErrorDetail
    error_detail_message: str = error_detail_field.__str__()

    assert (
        expected_error_message == error_detail_message
    ), f"Unexpected error message: {error_detail_message}"


@pytest.mark.django_db
def test_user_persistence(user_with_valid_fields: dict):
    """
    Tests if a user with valid data is correctly created and persisted in the database.
    """
    # Initialize the serializer with the user data
    serializer = UserSerializer(data=user_with_valid_fields)

    # Check if the serializer is valid and the user is persisted in the database
    assert serializer.is_valid(), "Serializer should be valid for valid data."
    user_id = serializer.save().id
    assert User.objects.filter(
        id=user_id
    ).exists(), "User was not persisted in the database."


@pytest.mark.django_db
def test_confirmation_password_not_persisted(user_with_valid_fields: dict):
    """
    Tests if the confirmation_password field is not persisted in the user model.
    """
    # Initialize the serializer with the user data
    serializer = UserSerializer(data=user_with_valid_fields)

    # Check if the serializer is valid and the confirmation_password field is not present in the saved object
    assert serializer.is_valid(), "Serializer should be valid for valid data."
    assert not hasattr(
        serializer.save(), "confirmation_password"
    ), "confirmation_password field should not be persisted, but it was."


@pytest.mark.django_db
def test_invalid_password_validation(user_with_invalid_passwords):
    """
    Tests if invalid password validation returns the expected errors.
    """
    expected_error_messages: list[str] = [
        "This password is too short. It must contain at least 8 characters.",
        "This password is too common.",
        "This password is entirely numeric.",
    ]

    # Initialize the serializer with the user data
    serializer = UserSerializer(data=user_with_invalid_passwords)

    # Check if the serializer is invalid
    assert (
        not serializer.is_valid()
    ), "Serializer should be invalid for invalid passwords."

    # Get the first error from the password field
    error_detail_field: ErrorDetail = serializer.errors.get("password", [])[0]
    # Get the message
    error_detail_message: str = error_detail_field.__str__()

    # Convert the error message to a list of strings
    errors_messages: list[str] = eval(error_detail_message)

    # Check if the error messages are as expected
    assert (
        expected_error_messages == errors_messages
    ), f"Unexpected error messages: {errors_messages}"
