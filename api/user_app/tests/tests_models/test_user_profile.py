"""
This module tests the creation and persistence in the database of a user profile.
"""

import pytest
from django.db import IntegrityError
from user_app.models import (
    AccountActivationCodeModel,
    BlacklistTokenModel,
    ChangeEmailCodeModel,
    PendingAccounts,
    ResetPasswordCodeModel,
    UserProfileModel,
    ValidTokenModel,
)

# ========== Constants ==================
EMAIL_UPPERCASE_DOMAIN = "fake_email@DOMAINUPPERCASE.com"


# ============ Fixtures =========================
@pytest.fixture
def user_data() -> dict[str, str]:
    """
    Returns default user data for use in tests.
    """

    return {
        "email": "fake@email.com",
        "password": "1234",
        "first_name": "fake_first_name",
        "last_name": "fake_last_name",
    }


# ============== Tests ==================
@pytest.mark.django_db
def test_creates_user_instance(user_data: dict):
    """
    Tests if a user instance is correctly created with the provided data.
    """

    actual_user = UserProfileModel.objects.create_user(**user_data)
    assert actual_user.email == user_data["email"]
    assert actual_user.check_password(user_data["password"])
    assert actual_user.first_name == user_data["first_name"]
    assert actual_user.last_name == user_data["last_name"]
    assert not actual_user.is_active
    assert not actual_user.is_staff
    assert not actual_user.is_superuser


@pytest.mark.django_db
def test_does_not_create_user_without_email(user_data: dict):
    """
    Tests if an error is raised when trying to create a user without an email.
    """

    del user_data["email"]
    with pytest.raises(TypeError):
        UserProfileModel.objects.create_user(**user_data)


@pytest.mark.django_db
def test_does_not_create_user_with_duplicate_email(user_data: dict):
    """
    Tests if an integrity error is raised when trying to create two users
    with the same email.
    """

    with pytest.raises(IntegrityError):
        UserProfileModel.objects.create_user(**user_data)
        UserProfileModel.objects.create_user(**user_data)


@pytest.mark.django_db
def test_does_not_create_user_without_password(user_data: dict):
    """
    Tests if an error is raised when trying to create a user without a password.
    """

    del user_data["password"]
    with pytest.raises(TypeError):
        UserProfileModel.objects.create_user(**user_data)


@pytest.mark.django_db
def test_creates_superuser(user_data: dict):
    """
    Tests if a superuser instance is correctly created with the provided data.
    """

    actual_superuser = UserProfileModel.objects.create_superuser(**user_data)
    assert actual_superuser.is_staff
    assert actual_superuser.is_superuser
    assert actual_superuser.is_active


@pytest.mark.django_db
def test_normalizes_email_domain(user_data):
    """
    Tests if the email domain is normalized to lowercase.
    """

    user_data["email"] = EMAIL_UPPERCASE_DOMAIN
    assert UserProfileModel.objects.create_user(**user_data).email.islower()


@pytest.mark.django_db
def test_user_deletion_cascades_to_related_models(user_data: dict):
    """
    Test that deleting a user also deletes all related models through cascading.
    """
    user = UserProfileModel.objects.create_user(**user_data)

    ValidTokenModel.objects.create(user=user, jti="fake", exp=1246468468, typ="access")
    BlacklistTokenModel.objects.create(
        user=user, jti="fake", exp=1246468468, typ="access"
    )
    AccountActivationCodeModel.objects.create(user=user)
    ChangeEmailCodeModel.objects.create(user=user)
    ResetPasswordCodeModel.objects.create(user=user)
    PendingAccounts.objects.create(user=user)

    assert ValidTokenModel.objects.exists()
    assert BlacklistTokenModel.objects.exists()
    assert AccountActivationCodeModel.objects.exists()
    assert ChangeEmailCodeModel.objects.exists()
    assert ResetPasswordCodeModel.objects.exists()
    assert PendingAccounts.objects.exists()

    user.delete()

    assert not ValidTokenModel.objects.exists()
    assert not BlacklistTokenModel.objects.exists()
    assert not AccountActivationCodeModel.objects.exists()
    assert not ChangeEmailCodeModel.objects.exists()
    assert not ResetPasswordCodeModel.objects.exists()
    assert not PendingAccounts.objects.exists()
