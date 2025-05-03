import pytest
from account_auth.models.code import (
    AccountActivationCodeModel,
    ChangeEmailCodeModel,
    ResetPasswordCodeModel,
)
from account_auth.tests.constants import Account

# =========== Objects and constants ==============
CODE_1 = "fakecode1"
CODE_2 = "fakecode2"
CODE_3 = "fakecode3"
NEWEST_CODE = "fakecode4"
ACCOUNT_EMAIL = "fakeemail@email.com"
FAKE_ACCOUNT_DATA = {
    "first_name": "fake_first_name",
    "last_name": "fake_last_name",
    "email": ACCOUNT_EMAIL,
    "password": "FAKEpassowrd1234!",
}


# ============ Fixtures ================
@pytest.fixture
def account_factory():
    """
    Creates and returns a Account object with mock data defined in FAKE_ACCOUNT_DATA.
    """
    return Account.objects.create_user(**FAKE_ACCOUNT_DATA)


@pytest.fixture
def add_change_email_codes(account_factory):
    """
    Adds multiple records to the ChangeEmailCodeModel for the account created in the
    account_factory fixture.
    """
    ChangeEmailCodeModel.objects.create(
        code=CODE_1, account=account_factory, new_email="new@email.com"
    )
    ChangeEmailCodeModel.objects.create(
        code=CODE_2, account=account_factory, new_email="new@email.com"
    )
    ChangeEmailCodeModel.objects.create(
        code=CODE_3, account=account_factory, new_email="new@email.com"
    )
    ChangeEmailCodeModel.objects.create(
        code=NEWEST_CODE, account=account_factory, new_email="new@email.com"
    )


@pytest.fixture
def add_activation_codes(account_factory):
    """
    Adds multiple records to the AccountActivationCodeModel for the account created in the
    account_factory fixture.
    """
    AccountActivationCodeModel.objects.create(code=CODE_1, account=account_factory)
    AccountActivationCodeModel.objects.create(code=CODE_2, account=account_factory)
    AccountActivationCodeModel.objects.create(code=CODE_3, account=account_factory)
    AccountActivationCodeModel.objects.create(code=NEWEST_CODE, account=account_factory)


@pytest.fixture
def add_reset_password_codes(account_factory):
    """
    Adds multiple records to the ResetPasswordCodeModel for the account created in the
    account_factory fixture.
    """
    ResetPasswordCodeModel.objects.create(code=CODE_1, account=account_factory)
    ResetPasswordCodeModel.objects.create(code=CODE_2, account=account_factory)
    ResetPasswordCodeModel.objects.create(code=CODE_3, account=account_factory)
    ResetPasswordCodeModel.objects.create(code=NEWEST_CODE, account=account_factory)


# ============ Tests ================
@pytest.mark.django_db
def test_keep_latest_change_email_code(add_change_email_codes):
    """
    Ensures that calling the keep_latest_code method correctly removes
    all codes except the most recent one for a specific account.

      Steps:
      - Verifies that older codes have been removed.
      - Confirms that only the most recent code exists in the database.
    """
    ChangeEmailCodeModel.objects.keep_latest_code(account_email=ACCOUNT_EMAIL)

    assert not ChangeEmailCodeModel.objects.filter(code=CODE_1).exists()
    assert not ChangeEmailCodeModel.objects.filter(code=CODE_2).exists()
    assert not ChangeEmailCodeModel.objects.filter(code=CODE_3).exists()
    assert ChangeEmailCodeModel.objects.filter(code=NEWEST_CODE).exists()
    assert ChangeEmailCodeModel.objects.filter(account_id=ACCOUNT_EMAIL).count() == 1


@pytest.mark.django_db
def test_keep_latest_activation_code(add_activation_codes):
    """
    Ensures that calling the keep_latest_code method correctly removes
    all codes except the most recent one for a specific account.

      Steps:
      - Verifies that older codes have been removed.
      - Confirms that only the most recent code exists in the database.
    """
    AccountActivationCodeModel.objects.keep_latest_code(account_email=ACCOUNT_EMAIL)

    assert not AccountActivationCodeModel.objects.filter(code=CODE_1).exists()
    assert not AccountActivationCodeModel.objects.filter(code=CODE_2).exists()
    assert not AccountActivationCodeModel.objects.filter(code=CODE_3).exists()
    assert AccountActivationCodeModel.objects.filter(code=NEWEST_CODE).exists()
    assert (
        AccountActivationCodeModel.objects.filter(account_id=ACCOUNT_EMAIL).count() == 1
    )


@pytest.mark.django_db
def test_keep_latest_reset_password_code(add_reset_password_codes):
    """
    Ensures that calling the keep_latest_code method correctly removes
    all codes except the most recent one for a specific account.

      Steps:
      - Verifies that older codes have been removed.
      - Confirms that only the most recent code exists in the database.
    """
    ResetPasswordCodeModel.objects.keep_latest_code(account_email=ACCOUNT_EMAIL)

    assert not ResetPasswordCodeModel.objects.filter(code=CODE_1).exists()
    assert not ResetPasswordCodeModel.objects.filter(code=CODE_2).exists()
    assert not ResetPasswordCodeModel.objects.filter(code=CODE_3).exists()
    assert ResetPasswordCodeModel.objects.filter(code=NEWEST_CODE).exists()
    assert ResetPasswordCodeModel.objects.filter(account_id=ACCOUNT_EMAIL).count() == 1
