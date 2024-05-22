import pytest
from django.contrib.auth import get_user_model  # type: ignore
from rest_framework.exceptions import ErrorDetail  # type: ignore

from user_app.serializers import UserRegistrationSerializer

User = get_user_model()


@pytest.fixture
def data_with_valid_fields():
    return {
        "email": "user@email.com",
        "password": "1234_!pass",
        "password_confirmation": "1234_!pass",
        "first_name": "my_name",
        "last_name": "my_last_name",
    }


@pytest.fixture
def data_with_unmateched_passwords():
    return {
        "email": "user@email.com",
        "password": "1234_!pass",
        "password_confirmation": "1234_!pass_unmatched",
        "first_name": "my_name",
        "last_name": "my_last_name",
    }


@pytest.mark.django_db
def unmatched_passwords_are_invalid(data_with_unmateched_passwords: dict):
    expected_error_message = "Password do not match"

    serializer = UserRegistrationSerializer(data=data_with_unmateched_passwords)

    assert not serializer.is_valid()
    assert serializer.errors["confirmation_password"] == expected_error_message


@pytest.mark.django_db
def test_persists_user(data_with_valid_fields: dict):
    serializer = UserRegistrationSerializer(data=data_with_valid_fields)

    assert serializer.is_valid()
    user = serializer.save()
    assert User.objects.filter(id=user.id).exists()


@pytest.mark.django_db
def test_persists_user_without_confirmation_passowrd_field(
    data_with_valid_fields: dict,
):
    serializer = UserRegistrationSerializer(data=data_with_valid_fields)

    assert serializer.is_valid()
    user = serializer.save()
    assert not hasattr(user, "confirmation_password")


@pytest.mark.django_db
def test_invalid_password():
    invalid_password = "1234"
    expected_error_messages: list[str] = [
        "This password is too short. It must contain at least 8 characters.",
        "This password is too common.",
        "This password is entirely numeric.",
    ]

    serializer = UserRegistrationSerializer(
        data={
            "first_name": "Willkimen",
            "last_name": "Cavalcanti",
            "email": "will@email.com",
            "password": invalid_password,
            "password_confirmation": invalid_password,
        }
    )

    assert not serializer.is_valid()

    error_detail_field: ErrorDetail = serializer.errors.get("password", [])[0]
    error_detail_message: str = error_detail_field.__str__()
    errors_messages: list[str] = eval(error_detail_message)

    assert expected_error_messages[0] == errors_messages[0]
    assert expected_error_messages[1] == errors_messages[1]
    assert expected_error_messages[2] == errors_messages[2]
