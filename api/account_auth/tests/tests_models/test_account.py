"""
This module tests the creation and persistence in the database of an account.
"""

import pytest
from django.db import IntegrityError
from account_auth.models import (
    AccountActivationCodeModel,
    AccountModel,
    BlacklistTokenModel,
    ChangeEmailCodeModel,
    PendingAccountsModel,
    ResetPasswordCodeModel,
    ValidTokenModel,
)

# ========== Constants ==================
EMAIL_UPPERCASE_DOMAIN = "fake_email@DOMAINUPPERCASE.com"


# ============ Fixtures =========================
@pytest.fixture
def account_data() -> dict[str, str]:
    """
    Returns default account data for use in tests.
    """

    return {
        "email": "fake@email.com",
        "password": "1234",
        "first_name": "fake_first_name",
        "last_name": "fake_last_name",
    }


# ============== Tests ==================
@pytest.mark.django_db
def test_creates_account_instance(account_data: dict):
    """
    Tests if an account instance is correctly created with the provided data.
    """

    actual_account = AccountModel.objects.create_user(**account_data)
    assert actual_account.email == account_data["email"]
    assert actual_account.check_password(account_data["password"])
    assert actual_account.first_name == account_data["first_name"]
    assert actual_account.last_name == account_data["last_name"]
    assert not actual_account.is_active
    assert not actual_account.is_staff
    assert not actual_account.is_superuser


@pytest.mark.django_db
def test_does_not_create_account_without_email(account_data: dict):
    """
    Tests if an error is raised when trying to create an account without an email.
    """

    del account_data["email"]
    with pytest.raises(TypeError):
        AccountModel.objects.create_user(**account_data)


@pytest.mark.django_db
def test_does_not_create_account_with_duplicate_email(account_data: dict):
    """
    Tests if an integrity error is raised when trying to create two accounts
    with the same email.
    """

    with pytest.raises(IntegrityError):
        AccountModel.objects.create_user(**account_data)
        AccountModel.objects.create_user(**account_data)


@pytest.mark.django_db
def test_does_not_create_account_without_password(account_data: dict):
    """
    Tests if an error is raised when trying to create an account without a password.
    """

    del account_data["password"]
    with pytest.raises(TypeError):
        AccountModel.objects.create_user(**account_data)


@pytest.mark.django_db
def test_creates_superuser(account_data: dict):
    """
    Tests if a superuser instance is correctly created with the provided data.
    """

    actual_superuser = AccountModel.objects.create_superuser(**account_data)
    assert actual_superuser.is_staff
    assert actual_superuser.is_superuser
    assert actual_superuser.is_active


@pytest.mark.django_db
def test_normalizes_email_domain(account_data):
    """
    Tests if the email domain is normalized to lowercase.
    """

    account_data["email"] = EMAIL_UPPERCASE_DOMAIN
    assert AccountModel.objects.create_user(**account_data).email.islower()


@pytest.mark.django_db
def test_account_deletion_cascades_to_related_models(account_data: dict):
    """
    Test that deleting an account also deletes all related models through cascading.
    """
    account = AccountModel.objects.create_user(**account_data)

    ValidTokenModel.objects.create(
        account=account, jti="fake", exp=1246468468, typ="access"
    )
    BlacklistTokenModel.objects.create(
        account=account, jti="fake", exp=1246468468, typ="access"
    )
    AccountActivationCodeModel.objects.create(account=account)
    ChangeEmailCodeModel.objects.create(account=account)
    ResetPasswordCodeModel.objects.create(account=account)
    PendingAccountsModel.objects.create(account=account)

    assert ValidTokenModel.objects.exists()
    assert BlacklistTokenModel.objects.exists()
    assert AccountActivationCodeModel.objects.exists()
    assert ChangeEmailCodeModel.objects.exists()
    assert ResetPasswordCodeModel.objects.exists()
    assert PendingAccountsModel.objects.exists()

    account.delete()

    assert not ValidTokenModel.objects.exists()
    assert not BlacklistTokenModel.objects.exists()
    assert not AccountActivationCodeModel.objects.exists()
    assert not ChangeEmailCodeModel.objects.exists()
    assert not ResetPasswordCodeModel.objects.exists()
    assert not PendingAccountsModel.objects.exists()
