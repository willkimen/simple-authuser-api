import smtplib
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from user_app.constants import response_messages

User = get_user_model()

url: str = reverse("register")


@pytest.fixture
def client() -> APIClient:
    """Returns an API client to make requests."""
    return APIClient()


@pytest.fixture
def user_registration_data() -> dict[str:str]:
    """Returns the user registration data for the request."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "johndoe@example.com",
        "password": "Password123!*",
        "confirmation_password": "Password123!*",
    }


@pytest.fixture
def expected_user_data() -> dict[str:str]:
    """Returns the expected user data in the database after creation."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "johndoe@example.com",
    }


@pytest.mark.django_db
@patch("user_app.views.send_activation_email")
def test_creates_user_with_valid_data(
    mock_send_activation_email,
    client: APIClient,
    user_registration_data: dict[str:str],
    expected_user_data: dict[str:str],
):
    """
    Tests if a new user is correctly created with valid data.

    Args:
        mock_send_activation_email (Mock): Mock of the activation email sending function.
        client (APIClient): API client to make requests.
        user_registration_data (dict): User registration data for the request.
        expected_user_data (dict): Expected user data in the database after creation.
    """

    # Define variables for expected status code and expected message
    expected_status_code = status.HTTP_201_CREATED
    expected_message = response_messages.USER_REGISTERED_SUCCESSFULLY
    # Make the POST request to register the user
    response = client.post(url, data=user_registration_data, format="json")

    # Add the created user's ID to the expected data and set the is_active field to False
    expected_user_data["id"] = response.data["user"]["id"]
    expected_user_data["is_active"] = False

    # Check if the user was created in the database with the expected data
    assert User.objects.filter(
        **expected_user_data
    ).exists(), "User was not created in the database with the expected data."

    # Check the response status code
    assert (
        expected_status_code == response.status_code
    ), f"Unexpected status code: {response.status_code}"

    # Check the success message in the response
    assert (
        expected_message == response.data["message"]
    ), f"Unexpected success message in the response. Expected: '{expected_message}'"

    # Check if the email sending function was called
    mock_send_activation_email.assert_called_once()


@pytest.mark.django_db
@patch("user_app.views.send_activation_email", side_effect=smtplib.SMTPException())
def test_does_not_create_user_when_email_sending_fails(
    mock_send_activation_email,
    client: APIClient,
    user_registration_data: dict[str, str],
):
    """
    Tests if user is not created when attempt to send email failed.

    Args:
        mock_send_activation_email(MagicMock): Mock object to send email function
        client (APIClient): API client to make requests.
        user_registration_data (dict): User registration data for the request.
    """

    expected_message = response_messages.ERROR_SENDING_EMAIL
    expected_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    response = client.post(url, data=user_registration_data, format="json")

    assert expected_message == response.data["message"]
    assert expected_code == response.status_code
    # Verify if user was not created
    assert not User.objects.filter(
        email=user_registration_data["email"]
    ).exists(), "User was not created in the database with the expected data."


@pytest.mark.parametrize(
    "invalid_email_format",
    [
        "email.com",
        "email@@domain.com",
        ".email@domain.com",
        "email.@domain.com",
        "em..ail@domain.com",
        "e mail@domain.com",
        "@domain.com",
        "email@",
        "email@domain",
        "email@domain..com",
        "email@[domain.com]",
        "email@domain.",
    ],
)
@pytest.mark.django_db
def test_does_not_create_user_with_invalid_email_format(
    invalid_email_format, client: APIClient, user_registration_data: dict[str, str]
):
    """
    Test if a user is not created when the email has an invalid format.

    Args:
        invalid_email_format (str): Invalid email format to be tested.
        client (APIClient): API client to make requests.
        user_registration_data (dict): User registration data for the request.
    """
    # Define variables for expected status code, expected field, and expected message
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_field = "email"
    expected_error_message = "Enter a valid email address."

    # Change the email field value to invalid formats
    user_registration_data["email"] = invalid_email_format

    # Make the POST request to register the user
    response = client.post(url, data=user_registration_data, format="json")

    # Check if the response status code is 400 BAD REQUEST
    assert (
        expected_status_code == response.status_code
    ), f"Unexpected status code: {response.status_code}"

    # Check if the 'email' field is present in the validation errors
    assert (
        expected_error_field in response.data["validation_errors"]
    ), f"'{expected_error_field}' is not present in the validation errors."

    # Check the error message
    assert (
        expected_error_message
        in response.data["validation_errors"][expected_error_field]
    ), f"Unexpected error message for '{expected_error_field}'. Expected: '{expected_error_message}'"


@pytest.mark.django_db
def test_does_not_create_user_with_duplicate_email(
    client: APIClient, user_registration_data: dict[str, str]
):
    """
    Tests if a user is not created when the email is already registered.

    Args:
        client (APIClient): API client to make requests.
        user_registration_data (dict): User registration data for the request.
    """
    # Define variables for expected status code, field, and error message
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_field = "email"
    expected_error_message = "User Profile with this email already exists."

    # Create a user with the provided email
    client.post(url, data=user_registration_data, format="json")

    # Try to create a second user with the same email
    response = client.post(url, data=user_registration_data, format="json")

    # Check if the response status code is 400 BAD REQUEST
    assert (
        expected_status_code == response.status_code
    ), f"Unexpected status code: {response.status_code}"

    # Check if the 'email' field is present in the validation errors
    assert (
        expected_error_field in response.data["validation_errors"]
    ), f"'{expected_error_field}' is not present in the validation errors."

    # Check the error message
    assert (
        expected_error_message
        in response.data["validation_errors"][expected_error_field]
    ), f"Unexpected error message for '{expected_error_field}'. Expected: '{expected_error_message}'"


@pytest.mark.django_db
def test_does_not_create_user_with_blank_email(
    client: APIClient, user_registration_data: dict[str, str]
):
    """
    Tests if a user is not created when the email is blank.

    Args:
        client (APIClient): API client to make requests.
        user_registration_data (dict[str, str]): User registration data for the request.
    """
    # Define variables for expected status code, field, and error message
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_field = "email"
    expected_error_message = "This field is required."

    # Remove the email field
    del user_registration_data["email"]

    # Make the POST request to register the user
    response = client.post(url, data=user_registration_data, format="json")

    # Check if the response status code is 400 BAD REQUEST
    assert (
        expected_status_code == response.status_code
    ), f"Unexpected status code: {response.status_code}"

    # Check if the 'email' field is present in the validation errors
    assert (
        expected_error_field in response.data["validation_errors"]
    ), f"'{expected_error_field}' is not present in the validation errors."

    # Check the error message
    assert (
        expected_error_message
        in response.data["validation_errors"][expected_error_field]
    ), f"Unexpected error message for '{expected_error_field}'. Expected: '{expected_error_message}'"


@pytest.mark.django_db
def test_does_not_create_user_with_null_email(
    client: APIClient, user_registration_data: dict[str, str]
):
    """
    Tests if a user is not created when the email is null.

    Args:
        client (APIClient): API client to make requests.
        user_registration_data (dict): User registration data for the request.
    """
    # Define variables for expected status code, field, and error message
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_field = "email"
    expected_error_message = "This field may not be null."

    # Set the email field to None
    user_registration_data["email"] = None

    # Make the POST request to register the user
    response = client.post(url, data=user_registration_data, format="json")

    # Check if the response status code is 400 BAD REQUEST
    assert (
        expected_status_code == response.status_code
    ), f"Unexpected status code: {response.status_code}"

    # Check if the 'email' field is present in the validation errors
    assert (
        expected_error_field in response.data["validation_errors"]
    ), f"'{expected_error_field}' is not present in the validation errors."

    # Check the error message
    assert (
        expected_error_message
        in response.data["validation_errors"][expected_error_field]
    ), f"Unexpected error message for '{expected_error_field}'. Expected: '{expected_error_message}'"


@pytest.mark.django_db
def test_passwords_not_in_response(
    client: APIClient, user_registration_data: dict[str, str]
):
    """
    Tests if the password and confirmation_password fields are not in the response.

    Args:
        client (APIClient): API client to make requests.
        user_registration_data (dict): User registration data for the request.
    """
    # Make the POST request to register the user
    response = client.post(url, data=user_registration_data, format="json")

    # Define variables for expected fields
    expected_absent_fields = ["password", "confirmation_password"]

    # Check if these fields are not in the response
    for field in expected_absent_fields:
        assert (
            field not in response.data["user"]
        ), f"'{field}' is present in the response."


@pytest.mark.django_db
def test_does_not_create_user_with_different_passwords(
    client: APIClient, user_registration_data: dict[str, str]
):
    """
    Tests if a user is not created when the provided passwords are different.

    Args:
        client (APIClient): API client to make requests.
        user_registration_data (dict): User registration data for the request.
    """
    # Define variables for expected status code, field, and error message
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_field = "confirmation_password"
    expected_error_message = "Passwords do not match"

    # Change the 'confirmation_password' field to a different password
    user_registration_data["confirmation_password"] = "DifferentPassword123!*"

    # Make the POST request to register the user
    response = client.post(url, data=user_registration_data, format="json")

    # Check if the response status code is 400 BAD REQUEST
    assert (
        expected_status_code == response.status_code
    ), f"Unexpected status code: {response.status_code}"

    # Check if the 'confirmation_password' field is present in the validation errors
    assert (
        expected_error_field in response.data["validation_errors"]
    ), f"'{expected_error_field}' is not present in the validation errors."

    # Check the error message
    assert (
        expected_error_message
        in response.data["validation_errors"][expected_error_field]
    ), f"Unexpected error message for '{expected_error_field}'. Expected: '{expected_error_message}'"


@pytest.mark.django_db
def test_does_not_create_user_with_short_password(
    client: APIClient, user_registration_data: dict[str, str]
):
    """
    Tests if a user is not created when the provided password is shorter than 8 characters.

    Args:
        client (APIClient): API client to make requests.
        user_registration_data (dict[str, str]): User registration data for the request.
    """
    # Define variables for expected status code, field, and error message
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_field = "password"
    expected_error_message = (
        "This password is too short. It must contain at least 8 characters."
    )

    # Change the 'password' field to a password shorter than 8 characters
    short_password = "abc!100"
    user_registration_data["password"] = short_password
    user_registration_data["confirmation_password"] = short_password

    # Make the POST request to register the user
    response = client.post(url, data=user_registration_data, format="json")

    # Check if the response status code is 400 BAD REQUEST
    assert (
        expected_status_code == response.status_code
    ), f"Unexpected status code: {response.status_code}"

    # Check if the 'password' field is present in the validation errors
    assert (
        expected_error_field in response.data["validation_errors"]
    ), f"'{expected_error_field}' is not present in the validation errors."

    # Check the error message
    assert (
        expected_error_message
        in response.data["validation_errors"][expected_error_field].__str__()
    ), f"Unexpected error message for '{expected_error_field}'. Expected: '{expected_error_message}'"


@pytest.mark.django_db
def test_does_not_create_user_with_numeric_password(
    client: APIClient, user_registration_data: dict[str, str]
):
    """
    Tests if a user is not created when the password is entirely numeric.

    Args:
        client (APIClient): API client to make requests.
        user_registration_data (dict[str, str]): User registration data for the request.
    """
    # Define variables for expected status code, field, and error message
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_field = "password"
    expected_error_message = "This password is entirely numeric."

    # Change the 'password' field to an entirely numeric password
    numeric_password = "12345678910"
    user_registration_data["password"] = numeric_password
    user_registration_data["confirmation_password"] = numeric_password

    # Make the POST request to register the user
    response = client.post(url, data=user_registration_data, format="json")

    # Check if the response status code is 400 BAD REQUEST
    assert (
        expected_status_code == response.status_code
    ), f"Unexpected status code: {response.status_code}"

    # Check if the 'password' field is present in the validation errors
    assert (
        expected_error_field in response.data["validation_errors"]
    ), f"'{expected_error_field}' is not present in the validation errors."

    # Check the error message
    assert (
        expected_error_message
        in response.data["validation_errors"][expected_error_field].__str__()
    ), f"Unexpected error message for '{expected_error_field}'. Expected: '{expected_error_message}'"


@pytest.mark.django_db
def test_does_not_create_user_with_common_password(
    client: APIClient, user_registration_data: dict[str, str]
):
    """
    Tests if a user is not created when the password is too common.

    Args:
        client (APIClient): API client to make requests.
        user_registration_data (dict[str, str]): User registration data for the request.
    """
    # Define variables for expected status code, field, and error message
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_field = "password"
    expected_error_message = "This password is too common."

    # Change the 'password' field to a common password
    common_password = "password123"
    user_registration_data["password"] = common_password
    user_registration_data["confirmation_password"] = common_password

    # Make the POST request to register the user
    response = client.post(url, data=user_registration_data, format="json")

    # Check if the response status code is 400 BAD REQUEST
    assert (
        expected_status_code == response.status_code
    ), f"Unexpected status code: {response.status_code}"

    # Check if the 'password' field is present in the validation errors
    assert (
        expected_error_field in response.data["validation_errors"]
    ), f"'{expected_error_field}' is not present in the validation errors."

    # Check the error message
    assert (
        expected_error_message
        in response.data["validation_errors"][expected_error_field].__str__()
    ), f"Unexpected error message for '{expected_error_field}'. Expected: '{expected_error_message}'"


@pytest.mark.django_db
def test_does_not_create_user_with_blank_first_name(
    client: APIClient, user_registration_data: dict[str, str]
):
    """
    Tests if a user is not created when the first_name is blank.

    Args:
        client (APIClient): API client to make requests.
        user_registration_data (dict[str, str]): User registration data for the request.
    """
    # Define variables for expected status code, field, and error message
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_field = "first_name"
    expected_error_message = "This field may not be blank."

    # Change the first_name field to an empty value
    user_registration_data["first_name"] = ""

    # Make the POST request to register the user
    response = client.post(url, data=user_registration_data, format="json")

    # Check if the response status code is 400 BAD REQUEST
    assert (
        expected_status_code == response.status_code
    ), f"Unexpected status code: {response.status_code}"

    # Check if the 'first_name' field is present in the validation errors
    assert (
        expected_error_field in response.data["validation_errors"]
    ), f"'{expected_error_field}' is not present in the validation errors."

    # Check the error message
    assert (
        expected_error_message
        in response.data["validation_errors"][expected_error_field]
    ), f"Unexpected error message for '{expected_error_field}'. Expected: '{expected_error_message}'"


@pytest.mark.django_db
def test_does_not_create_user_with_null_first_name(
    client: APIClient, user_registration_data: dict[str, str]
):
    """
    Tests if a user is not created when the first_name is null.

    Args:
        client (APIClient): API client to make requests.
        user_registration_data (dict[str, str]): User registration data for the request.
    """
    # Define variables for expected status code, field, and error message
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_field = "first_name"
    expected_error_message = "This field may not be null."

    # Change the first_name field to None
    user_registration_data["first_name"] = None

    response = client.post(url, data=user_registration_data, format="json")

    # Check if the response status code is 400 BAD REQUEST
    assert (
        expected_status_code == response.status_code
    ), f"Unexpected status code: {response.status_code}"

    # Check if the 'first_name' field is present in the validation errors
    assert (
        expected_error_field in response.data["validation_errors"]
    ), f"'{expected_error_field}' is not present in the validation errors."

    # Check the error message
    assert (
        expected_error_message
        in response.data["validation_errors"][expected_error_field]
    ), f"Unexpected error message for '{expected_error_field}'. Expected: '{expected_error_message}'"


@pytest.mark.django_db
def test_does_not_create_user_with_too_long_first_name(
    client: APIClient, user_registration_data: dict[str, str]
):
    """
    Tests if a user is not created when the first_name is too long.

    Args:
        client (APIClient): API client to make requests.
        user_registration_data (dict[str, str]): User registration data for the request.
    """
    # Define variables for expected status code, field, and error message
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_field = "first_name"
    expected_error_message = "Ensure this field has no more than 100 characters."

    # Change the first_name field to a very long value
    user_registration_data["first_name"] = "my_name" * 15

    response = client.post(url, data=user_registration_data, format="json")

    # Check if the response status code is 400 BAD REQUEST
    assert (
        expected_status_code == response.status_code
    ), f"Unexpected status code: {response.status_code}"

    # Check if the 'first_name' field is present in the validation errors
    assert (
        expected_error_field in response.data["validation_errors"]
    ), f"'{expected_error_field}' is not present in the validation errors."

    # Check the error message
    assert (
        expected_error_message
        in response.data["validation_errors"][expected_error_field]
    ), f"Unexpected error message for '{expected_error_field}'. Expected: '{expected_error_message}'"


@pytest.mark.django_db
def test_does_not_create_user_with_blank_last_name(
    client: APIClient, user_registration_data: dict[str, str]
):
    """
    Tests if a user is not created when the last_name is blank.

    Args:
        client (APIClient): API client to make requests.
        user_registration_data (dict[str, str]): User registration data for the request.
    """
    # Define variables for expected status code, field, and error message
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_field = "last_name"
    expected_error_message = "This field may not be blank."

    # Change the last_name field to an empty value
    user_registration_data["last_name"] = ""

    # Make the POST request to register the user
    response = client.post(url, data=user_registration_data, format="json")

    # Check if the response status code is 400 BAD REQUEST
    assert (
        expected_status_code == response.status_code
    ), f"Unexpected status code: {response.status_code}"

    # Check if the 'last_name' field is present in the validation errors
    assert (
        expected_error_field in response.data["validation_errors"]
    ), f"'{expected_error_field}' is not present in the validation errors."

    # Check the error message
    assert (
        expected_error_message
        in response.data["validation_errors"][expected_error_field]
    ), f"Unexpected error message for '{expected_error_field}'. Expected: '{expected_error_message}'"


@pytest.mark.django_db
def test_does_not_create_user_with_null_last_name(
    client: APIClient, user_registration_data: dict[str, str]
):
    """
    Tests if a user is not created when the last_name is null.

    Args:
        client (APIClient): API client to make requests.
        user_registration_data (dict[str, str]): User registration data for the request.
    """
    # Define variables for expected status code, field, and error message
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_field = "last_name"
    expected_error_message = "This field may not be null."

    # Change the last_name field to None
    user_registration_data["last_name"] = None

    response = client.post(url, data=user_registration_data, format="json")

    # Check if the response status code is 400 BAD REQUEST
    assert (
        expected_status_code == response.status_code
    ), f"Unexpected status code: {response.status_code}"

    # Check if the 'last_name' field is present in the validation errors
    assert (
        expected_error_field in response.data["validation_errors"]
    ), f"'{expected_error_field}' is not present in the validation errors."

    # Check the error message
    assert (
        expected_error_message
        in response.data["validation_errors"][expected_error_field]
    ), f"Unexpected error message for '{expected_error_field}'. Expected: '{expected_error_message}'"


@pytest.mark.django_db
def test_does_not_create_user_with_too_long_last_name(
    client: APIClient, user_registration_data: dict[str, str]
):
    """
    Tests if a user is not created when the last_name is too long.

    Args:
        client (APIClient): API client to make requests.
        user_registration_data (dict[str, str]): User registration data for the request.
    """
    # Define variables for expected status code, field, and error message
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_field = "last_name"
    expected_error_message = "Ensure this field has no more than 100 characters."

    # Change the last_name field to a very long value
    user_registration_data["last_name"] = "my_name" * 15

    response = client.post(url, data=user_registration_data, format="json")

    # Check if the response status code is 400 BAD REQUEST
    assert (
        expected_status_code == response.status_code
    ), f"Unexpected status code: {response.status_code}"

    # Check if the 'last_name' field is present in the validation errors
    assert (
        expected_error_field in response.data["validation_errors"]
    ), f"'{expected_error_field}' is not present in the validation errors."

    # Check the error message
    assert (
        expected_error_message
        in response.data["validation_errors"][expected_error_field]
    ), f"Unexpected error message for '{expected_error_field}'. Expected: '{expected_error_message}'"
