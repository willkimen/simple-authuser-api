import pytest
from user_app.models.code_models import (
    AccountActivationCodeModel,
    ChangeEmailCodeModel,
    ResetPasswordCodeModel,
)
from user_app.tests.constants import User

# =========== Objects and constants ==============
CODE_1 = "fakecode1"
CODE_2 = "fakecode2"
CODE_3 = "fakecode3"
NEWEST_CODE = "fakecode4"
USER_EMAIL = "fakeemail@email.com"
FAKE_USER_DATA = {
    "first_name": "fake_first_name",
    "last_name": "fake_last_name",
    "email": USER_EMAIL,
    "password": "FAKEpassowrd1234!",
}


# ============ Fixtures ================
@pytest.fixture
def user_factory():
    """
    Creates and returns a User object with mock data defined in FAKE_USER_DATA.
    """
    return User.objects.create_user(**FAKE_USER_DATA)


@pytest.fixture
def add_change_email_codes(user_factory):
    """
    Adds multiple records to the ChangeEmailCodeModel for the user created in the
    user_factory fixture.
    """
    ChangeEmailCodeModel.objects.create(
        code=CODE_1, user=user_factory, new_email="new@email.com"
    )
    ChangeEmailCodeModel.objects.create(
        code=CODE_2, user=user_factory, new_email="new@email.com"
    )
    ChangeEmailCodeModel.objects.create(
        code=CODE_3, user=user_factory, new_email="new@email.com"
    )
    ChangeEmailCodeModel.objects.create(
        code=NEWEST_CODE, user=user_factory, new_email="new@email.com"
    )


@pytest.fixture
def add_activation_codes(user_factory):
    """
    Adds multiple records to the AccountActivationCodeModel for the user created in the
    user_factory fixture.
    """
    AccountActivationCodeModel.objects.create(code=CODE_1, user=user_factory)
    AccountActivationCodeModel.objects.create(code=CODE_2, user=user_factory)
    AccountActivationCodeModel.objects.create(code=CODE_3, user=user_factory)
    AccountActivationCodeModel.objects.create(code=NEWEST_CODE, user=user_factory)


@pytest.fixture
def add_reset_password_codes(user_factory):
    """
    Adds multiple records to the ResetPasswordCodeModel for the user created in the
    user_factory fixture.
    """
    ResetPasswordCodeModel.objects.create(code=CODE_1, user=user_factory)
    ResetPasswordCodeModel.objects.create(code=CODE_2, user=user_factory)
    ResetPasswordCodeModel.objects.create(code=CODE_3, user=user_factory)
    ResetPasswordCodeModel.objects.create(code=NEWEST_CODE, user=user_factory)


# ============ Tests ================
@pytest.mark.django_db
def test_keep_latest_change_email_code(add_change_email_codes):
    """
    Ensures that calling the keep_latest_code method correctly removes
    all codes except the most recent one for a specific user.

      Steps:
      - Verifies that older codes have been removed.
      - Confirms that only the most recent code exists in the database.
    """
    ChangeEmailCodeModel.objects.keep_latest_code(user_email=USER_EMAIL)

    assert not ChangeEmailCodeModel.objects.filter(code=CODE_1).exists()
    assert not ChangeEmailCodeModel.objects.filter(code=CODE_2).exists()
    assert not ChangeEmailCodeModel.objects.filter(code=CODE_3).exists()
    assert ChangeEmailCodeModel.objects.filter(code=NEWEST_CODE).exists()
    assert ChangeEmailCodeModel.objects.filter(user_id=USER_EMAIL).count() == 1


@pytest.mark.django_db
def test_keep_latest_activation_code(add_activation_codes):
    """
    Ensures that calling the keep_latest_code method correctly removes
    all codes except the most recent one for a specific user.

      Steps:
      - Verifies that older codes have been removed.
      - Confirms that only the most recent code exists in the database.
    """
    AccountActivationCodeModel.objects.keep_latest_code(user_email=USER_EMAIL)

    assert not AccountActivationCodeModel.objects.filter(code=CODE_1).exists()
    assert not AccountActivationCodeModel.objects.filter(code=CODE_2).exists()
    assert not AccountActivationCodeModel.objects.filter(code=CODE_3).exists()
    assert AccountActivationCodeModel.objects.filter(code=NEWEST_CODE).exists()
    assert AccountActivationCodeModel.objects.filter(user_id=USER_EMAIL).count() == 1


@pytest.mark.django_db
def test_keep_latest_reset_password_code(add_reset_password_codes):
    """
    Ensures that calling the keep_latest_code method correctly removes
    all codes except the most recent one for a specific user.

      Steps:
      - Verifies that older codes have been removed.
      - Confirms that only the most recent code exists in the database.
    """
    ResetPasswordCodeModel.objects.keep_latest_code(user_email=USER_EMAIL)

    assert not ResetPasswordCodeModel.objects.filter(code=CODE_1).exists()
    assert not ResetPasswordCodeModel.objects.filter(code=CODE_2).exists()
    assert not ResetPasswordCodeModel.objects.filter(code=CODE_3).exists()
    assert ResetPasswordCodeModel.objects.filter(code=NEWEST_CODE).exists()
    assert ResetPasswordCodeModel.objects.filter(user_id=USER_EMAIL).count() == 1
