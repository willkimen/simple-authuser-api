import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from user_app.constants import response_codes_and_messages, validation_error_messages
from user_app.tests.constants import User

# ============== Objects and constants ==============
url: str = reverse("register")


# ============== Fixtures ================
@pytest.fixture
def client() -> APIClient:
    """Returns an API client to make requests."""
    return APIClient()


@pytest.fixture
def user_data() -> dict[str:str]:
    """Returns the user registration data for the request."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "johndoe@example.com",
        "password": "Password123!*",
        "confirmation_password": "Password123!*",
    }


# ================ Tests ==================
@pytest.mark.django_db
def test_creates_user_with_valid_data(
    client: APIClient,
    user_data: dict[str:str],
):
    """
    Tests if a new user is correctly created with valid data.

    Args:
        client (APIClient): API client to make requests.
        user_data (dict): User registration data for the request.
    """

    expected_status_code = status.HTTP_201_CREATED
    expected_detail_message = response_codes_and_messages.USER_REGISTERED_SUCCESSFULLY[
        "detail"
    ]
    expected_code = response_codes_and_messages.USER_REGISTERED_SUCCESSFULLY["code"]
    actual_response = client.post(url, data=user_data, format="json")

    # Check if the user was created in the database with the expected data
    assert User.objects.filter(**actual_response.data["user"]).exists()
    # Check if user was created with deactivated account.
    assert False == actual_response.data["user"]["is_active"]
    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


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
    invalid_email_format, client: APIClient, user_data: dict[str, str]
):
    """
    Test if a user is not created when the email has an invalid format.

    Args:
        invalid_email_format (str): Invalid email format to be tested.
        client (APIClient): API client to make requests.
        user_data (dict): User registration data for the request.
    """
    # Define variables for expected status code, expected field, and expected message
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_code = response_codes_and_messages.VALIDATION_ERRORS["code"]
    expected_detail_message = response_codes_and_messages.VALIDATION_ERRORS["detail"]
    expected_error_message_field = validation_error_messages.INVALID_FORMAT_EMAIL

    # Change the email field value to invalid formats
    user_data["email"] = invalid_email_format

    actual_response = client.post(url, data=user_data, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
    assert (
        expected_error_message_field
        in actual_response.data["field_errors"]["email"].__str__()
    )


@pytest.mark.django_db
def test_does_not_create_user_with_duplicate_email(
    client: APIClient,
    user_data: dict[str, str],
):
    """
    Tests if a user is not created when the email is already registered.

    Args:
        client (APIClient): API client to make requests.
        user_data (dict): User registration data for the request.
    """
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_message_field = validation_error_messages.EMAIL_ALREADY_EXISTS
    expected_code = response_codes_and_messages.VALIDATION_ERRORS["code"]
    expected_detail_message = response_codes_and_messages.VALIDATION_ERRORS["detail"]

    # Create a user with the provided email
    client.post(url, data=user_data, format="json")

    # Try to create a second user with the same email
    actual_response = client.post(url, data=user_data, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert (
        expected_error_message_field
        in actual_response.data["field_errors"]["email"].__str__()
    )


@pytest.mark.django_db
def test_does_not_create_user_with_blank_email(
    client: APIClient, user_data: dict[str, str]
):
    """
    Tests if a user is not created when the email is blank.

    Args:
        client (APIClient): API client to make requests.
        user_data (dict[str, str]): User registration data for the request.
    """
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_message_field = validation_error_messages.REQUIRED_FIELD
    expected_code = response_codes_and_messages.VALIDATION_ERRORS["code"]
    expected_detail_message = response_codes_and_messages.VALIDATION_ERRORS["detail"]

    # Remove the email field
    del user_data["email"]

    actual_response = client.post(url, data=user_data, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert (
        expected_error_message_field
        in actual_response.data["field_errors"]["email"].__str__()
    )


@pytest.mark.django_db
def test_does_not_create_user_with_null_email(
    client: APIClient, user_data: dict[str, str]
):
    """
    Tests if a user is not created when the email is null.

    Args:
        client (APIClient): API client to make requests.
        user_data (dict): User registration data for the request.
    """
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_message_field = validation_error_messages.NULL_FIELD
    expected_code = response_codes_and_messages.VALIDATION_ERRORS["code"]
    expected_detail_message = response_codes_and_messages.VALIDATION_ERRORS["detail"]

    # Set the email field to None
    user_data["email"] = None

    actual_response = client.post(url, data=user_data, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert (
        expected_error_message_field
        in actual_response.data["field_errors"]["email"].__str__()
    )


@pytest.mark.django_db
def test_passwords_not_in_response(
    client: APIClient,
    user_data: dict[str, str],
):
    """
    Tests if the password and confirmation_password fields are not in the response.

    Args:
        client (APIClient): API client to make requests.
        user_data (dict): User registration data for the request.
    """
    actual_response = client.post(url, data=user_data, format="json")

    # Check if these fields are not in the response
    assert "password" and "confirmation_passoword" not in actual_response.data["user"]


@pytest.mark.django_db
def test_does_not_create_user_with_different_passwords(
    client: APIClient, user_data: dict[str, str]
):
    """
    Tests if a user is not created when the provided passwords are different.

    Args:
        client (APIClient): API client to make requests.
        user_data (dict): User registration data for the request.
    """
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_message_field = validation_error_messages.PASSWORD_DO_NOT_MATCH
    expected_code = response_codes_and_messages.VALIDATION_ERRORS["code"]
    expected_detail_message = response_codes_and_messages.VALIDATION_ERRORS["detail"]

    # Change the 'confirmation_password' field to a different password
    user_data["confirmation_password"] = "DifferentPassword123!*"

    actual_response = client.post(url, data=user_data, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert (
        expected_error_message_field
        in actual_response.data["field_errors"]["confirmation_password"].__str__()
    )


@pytest.mark.django_db
def test_does_not_create_user_with_short_password(
    client: APIClient, user_data: dict[str, str]
):
    """
    Tests if a user is not created when the provided password
    is shorter than 8 characters.

    Args:
        client (APIClient): API client to make requests.
        user_data (dict[str, str]): User registration data for the request.
    """
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_message_field = validation_error_messages.SHORT_PASSWORD
    expected_code = response_codes_and_messages.VALIDATION_ERRORS["code"]
    expected_detail_message = response_codes_and_messages.VALIDATION_ERRORS["detail"]

    # Change the fields to a password shorter than 8 characters
    user_data["password"] = user_data["confirmation_password"] = "abc!100"

    actual_response = client.post(url, data=user_data, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert (
        expected_error_message_field
        in actual_response.data["field_errors"]["password"].__str__()
    )


@pytest.mark.django_db
def test_does_not_create_user_with_numeric_password(
    client: APIClient, user_data: dict[str, str]
):
    """
    Tests if a user is not created when the password is entirely numeric.

    Args:
        client (APIClient): API client to make requests.
        user_data (dict[str, str]): User registration data for the request.
    """
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_message_field = validation_error_messages.NUMERIC_PASSWORD
    expected_code = response_codes_and_messages.VALIDATION_ERRORS["code"]
    expected_detail_message = response_codes_and_messages.VALIDATION_ERRORS["detail"]

    # Change the fields to an entirely numeric password.
    user_data["password"] = user_data["confirmation_password"] = "12345678910"

    actual_response = client.post(url, data=user_data, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert (
        expected_error_message_field
        in actual_response.data["field_errors"]["password"].__str__()
    )


@pytest.mark.django_db
def test_does_not_create_user_with_common_password(
    client: APIClient, user_data: dict[str, str]
):
    """
    Tests if a user is not created when the password is too common.

    Args:
        client (APIClient): API client to make requests.
        user_data (dict[str, str]): User registration data for the request.
    """
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_message_field = validation_error_messages.COMMON_PASSWORD
    expected_code = response_codes_and_messages.VALIDATION_ERRORS["code"]
    expected_detail_message = response_codes_and_messages.VALIDATION_ERRORS["detail"]

    # Change the fields to a common password.
    user_data["password"] = user_data["confirmation_password"] = "password123"

    actual_response = client.post(url, data=user_data, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert (
        expected_error_message_field
        in actual_response.data["field_errors"]["password"].__str__()
    )


@pytest.mark.django_db
def test_does_not_create_user_with_blank_first_name(
    client: APIClient, user_data: dict[str, str]
):
    """
    Tests if a user is not created when the first_name is blank.

    Args:
        client (APIClient): API client to make requests.
        user_data (dict[str, str]): User registration data for the request.
    """
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_message_field = validation_error_messages.BLANK_FIELD
    expected_code = response_codes_and_messages.VALIDATION_ERRORS["code"]
    expected_detail_message = response_codes_and_messages.VALIDATION_ERRORS["detail"]

    # Change the first_name field to an empty value.
    user_data["first_name"] = ""

    actual_response = client.post(url, data=user_data, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert (
        expected_error_message_field
        in actual_response.data["field_errors"]["first_name"].__str__()
    )


@pytest.mark.django_db
def test_does_not_create_user_with_null_first_name(
    client: APIClient, user_data: dict[str, str]
):
    """
    Tests if a user is not created when the first_name is null.

    Args:
        client (APIClient): API client to make requests.
        user_data (dict[str, str]): User registration data for the request.
    """
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_message_field = validation_error_messages.NULL_FIELD
    expected_code = response_codes_and_messages.VALIDATION_ERRORS["code"]
    expected_detail_message = response_codes_and_messages.VALIDATION_ERRORS["detail"]

    # Change the first_name field to None
    user_data["first_name"] = None

    actual_response = client.post(url, data=user_data, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert (
        expected_error_message_field
        in actual_response.data["field_errors"]["first_name"].__str__()
    )


@pytest.mark.django_db
def test_does_not_create_user_with_too_long_first_name(
    client: APIClient, user_data: dict[str, str]
):
    """
    Tests if a user is not created when the first_name is too long.

    Args:
        client (APIClient): API client to make requests.
        user_data (dict[str, str]): User registration data for the request.
    """
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_message_field = validation_error_messages.LONG_FIELD
    expected_code = response_codes_and_messages.VALIDATION_ERRORS["code"]
    expected_detail_message = response_codes_and_messages.VALIDATION_ERRORS["detail"]

    # Change the first_name field to a very long value
    user_data["first_name"] = "my_name" * 15

    actual_response = client.post(url, data=user_data, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert (
        expected_error_message_field
        in actual_response.data["field_errors"]["first_name"].__str__()
    )


@pytest.mark.django_db
def test_does_not_create_user_with_blank_last_name(
    client: APIClient, user_data: dict[str, str]
):
    """
    Tests if a user is not created when the last_name is blank.

    Args:
        client (APIClient): API client to make requests.
        user_data (dict[str, str]): User registration data for the request.
    """
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_message_field = validation_error_messages.BLANK_FIELD
    expected_code = response_codes_and_messages.VALIDATION_ERRORS["code"]
    expected_detail_message = response_codes_and_messages.VALIDATION_ERRORS["detail"]

    user_data["last_name"] = ""

    actual_response = client.post(url, data=user_data, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert (
        expected_error_message_field
        in actual_response.data["field_errors"]["last_name"].__str__()
    )


@pytest.mark.django_db
def test_does_not_create_user_with_null_last_name(
    client: APIClient, user_data: dict[str, str]
):
    """
    Tests if a user is not created when the last_name is null.

    Args:
        client (APIClient): API client to make requests.
        user_data (dict[str, str]): User registration data for the request.
    """
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_message_field = validation_error_messages.NULL_FIELD
    expected_code = response_codes_and_messages.VALIDATION_ERRORS["code"]
    expected_detail_message = response_codes_and_messages.VALIDATION_ERRORS["detail"]

    # Change the last_name field to None
    user_data["last_name"] = None

    actual_response = client.post(url, data=user_data, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert (
        expected_error_message_field
        in actual_response.data["field_errors"]["last_name"].__str__()
    )


@pytest.mark.django_db
def test_does_not_create_user_with_too_long_last_name(
    client: APIClient, user_data: dict[str, str]
):
    """
    Tests if a user is not created when the last_name is too long.

    Args:
        client (APIClient): API client to make requests.
        user_data (dict[str, str]): User registration data for the request.
    """
    expected_status_code = status.HTTP_400_BAD_REQUEST
    expected_error_message_field = validation_error_messages.LONG_FIELD
    expected_code = response_codes_and_messages.VALIDATION_ERRORS["code"]
    expected_detail_message = response_codes_and_messages.VALIDATION_ERRORS["detail"]

    # Change the last_name field to a very long value
    user_data["last_name"] = "my_name" * 15

    actual_response = client.post(url, data=user_data, format="json")

    assert expected_status_code == actual_response.status_code
    assert expected_code == actual_response.data["code"]
    assert expected_detail_message == actual_response.data["detail"]
    assert (
        expected_error_message_field
        in actual_response.data["field_errors"]["last_name"].__str__()
    )
