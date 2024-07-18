import pytest
from django.db import IntegrityError

from user_app.models import UserProfile


@pytest.fixture
def user_data():
    """
    Returns default user data for use in tests.

    Returns:
        dict: User data.
    """
    return {
        "email": "user@email.com",
        "password": "1234",
        "first_name": "my_name",
        "last_name": "my_last_name",
    }


@pytest.mark.django_db
def test_creates_user_instance(user_data):
    """
    Tests if a user instance is correctly created with the provided data.
    """
    user_instance = UserProfile.objects.create_user(**user_data)

    assert user_instance.email == user_data["email"], "User email does not match."

    assert user_instance.check_password(
        user_data["password"]
    ), "User password does not match."

    assert (
        user_instance.first_name == user_data["first_name"]
    ), "User first name does not match."

    assert (
        user_instance.last_name == user_data["last_name"]
    ), "User last name does not match."

    assert not user_instance.is_active
    assert not user_instance.is_staff, "User should not be staff."
    assert not user_instance.is_superuser, "User should not be superuser."


@pytest.mark.django_db
def test_does_not_create_user_without_email(user_data):
    """
    Tests if an error is raised when trying to create a user without an email.
    """
    del user_data["email"]
    with pytest.raises(TypeError):
        UserProfile.objects.create_user(**user_data)


@pytest.mark.django_db
def test_normalizes_email_domain(user_data):
    """
    Tests if the email domain is normalized to lowercase.
    """
    user_data["email"] = "email@DOMAINUPPERCASE.com"
    user = UserProfile.objects.create_user(**user_data)

    assert user.email.islower(), "Email domain was not normalized to lowercase."


@pytest.mark.django_db
def test_does_not_create_user_with_duplicate_email(user_data):
    """
    Tests if an integrity error is raised when trying to create two users with the same email.
    """
    with pytest.raises(IntegrityError):
        UserProfile.objects.create_user(**user_data)
        UserProfile.objects.create_user(**user_data)


@pytest.mark.django_db
def test_does_not_create_user_without_password(user_data):
    """
    Tests if an error is raised when trying to create a user without a password.
    """
    del user_data["password"]
    with pytest.raises(TypeError):
        UserProfile.objects.create_user(**user_data)


@pytest.mark.django_db
def test_creates_superuser(user_data):
    """
    Tests if a superuser instance is correctly created with the provided data.
    """
    superuser = UserProfile.objects.create_superuser(**user_data)

    assert superuser.is_staff, "Superuser should be staff."
    assert superuser.is_superuser, "Superuser should be superuser."
    assert superuser.is_active
