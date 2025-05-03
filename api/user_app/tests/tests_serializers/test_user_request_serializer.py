"""
This module performs several tests related to errors and success in validating 
Account data, using AccountSerializer.
"""

import pytest
from rest_framework.exceptions import ErrorDetail
from user_app.constants import validation_error_messages
from user_app.serializers import AccountRequestSerializer
from user_app.tests.constants import Account

# ========== Objects and constants ============
CONFIRMATION_PASSWORD_DIFFERENCE = "1234_!Fake_difference"
INVALID_PASSWORD = "1234"


# ============== Fixtures  ======================
@pytest.fixture
def valid_account_data() -> dict[str, str]:
    """
    Returns valid data for a new account.
    """

    return {
        "email": "fake@email.com",
        "password": "1234_!Fake",
        "confirmation_password": "1234_!Fake",
        "first_name": "fake_first_name",
        "last_name": "fake_last_name",
    }


@pytest.fixture
def account_data_with_mismatched_passwords(valid_account_data: dict) -> dict[str, str]:
    """
    Returns account data where the passwords do not match.
    """
    valid_account_data["confirmation_password"] = CONFIRMATION_PASSWORD_DIFFERENCE
    return valid_account_data


@pytest.fixture
def account_data_with_invalid_passwords(valid_account_data: dict) -> dict[str, str]:
    """
    Returns account data with an invalid password.
    """
    # Set an invalid password for both keys on the same line.
    valid_account_data["password"] = valid_account_data["confirmation_password"] = (
        INVALID_PASSWORD
    )
    return valid_account_data


# ============== Tests ==================
@pytest.mark.django_db
def test_account_persisted_successfully(valid_account_data: dict):
    """
    Tests if an account with valid data is correctly created and persisted in the database.
    """
    # Initialize the serializer with the account data
    actual_serializer = AccountRequestSerializer(data=valid_account_data)

    # Check if the serializer is valid and the account is persisted in the database
    assert actual_serializer.is_valid()
    id = actual_serializer.save().id
    assert Account.objects.filter(id=id).exists()


@pytest.mark.django_db
def test_serializer_does_not_should_return_sensitive_fields(valid_account_data: dict):
    """
    Tests if the serializer does not return
    fields like passoword and confirmation_password
    """
    actual_serializer = AccountRequestSerializer(data=valid_account_data)

    assert actual_serializer.is_valid()
    assert "password" and "confirmation_password" not in actual_serializer.data


@pytest.mark.django_db
def test_invalid_when_passwords_differ(account_data_with_mismatched_passwords: dict):
    """
    Tests if an error is raised when the passwords do not match.
    """
    expected_error_message = validation_error_messages.PASSWORD_DO_NOT_MATCH

    # Initialize the serializer with the account data
    actual_serializer = AccountRequestSerializer(
        data=account_data_with_mismatched_passwords
    )

    # Check if the serializer is invalid and the error message is as expected
    assert not actual_serializer.is_valid()

    # Get the ErrorDetail object containing the error message
    # for the confirmation_password field
    error_detail_field: ErrorDetail = actual_serializer.errors.get(
        "confirmation_password", []
    )[0]

    # Get the message from the ErrorDetail
    actual_error_message = error_detail_field.__str__()

    assert expected_error_message == actual_error_message


@pytest.mark.django_db
def test_confirmation_password_field_not_persisted(valid_account_data: dict):
    """
    Tests if the confirmation_password field is not persisted in the account model.
    """
    # Initialize the serializer with the account data
    actual_serializer = AccountRequestSerializer(data=valid_account_data)

    # Check if the serializer is valid and the confirmation_password field
    # is not present in the saved object
    assert actual_serializer.is_valid()
    assert not hasattr(actual_serializer.save(), "confirmation_password")


@pytest.mark.django_db
def test_invalid_password_validation(account_data_with_invalid_passwords: dict):
    """
    Tests if invalid password validation returns the expected errors.
    """
    expected_error_messages: list[str] = [
        validation_error_messages.SHORT_PASSWORD,
        validation_error_messages.COMMON_PASSWORD,
        validation_error_messages.NUMERIC_PASSWORD,
    ]

    # Initialize the serializer with the account data
    actual_serializer = AccountRequestSerializer(
        data=account_data_with_invalid_passwords
    )

    # Check if the serializer is invalid
    assert not actual_serializer.is_valid()

    # Get the first error from the password field
    error_detail_field: ErrorDetail = actual_serializer.errors.get("password", [])[0]
    # Get the message
    error_detail_message: str = error_detail_field.__str__()

    # Convert the error message to a list of strings
    actual_errors_messages: list[str] = eval(error_detail_message)

    # Check if the error messages are as expected
    assert expected_error_messages == actual_errors_messages
