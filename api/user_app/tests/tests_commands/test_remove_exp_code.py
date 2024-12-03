"""
Tests the removal of expired codes from the tables related to account activation, 
email change, and password reset.

Models tested:
- `AccountActivationCodeModel`
- `ChangeEmailCodeModel`
- `ResetPasswordCodeModel`

Command tested:
- `remove_exp_code`
"""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from user_app.models import (
    AccountActivationCodeModel,
    ChangeEmailCodeModel,
    ResetPasswordCodeModel,
)

# ========== Objects and constants ============
User = get_user_model()


# ============== Fixtures  ======================
@pytest.fixture
def user():
    """
    Creates and returns a mock user object for testing purposes.
    """
    user_data = {
        "email": "fake@email.com",
        "password": "1234_!Fake",
        "first_name": "fake_first_name",
        "last_name": "fake_last_name",
    }

    return User.objects.create_user(**user_data)


# ============== Tests ==================
@pytest.mark.django_db
def test_remove_exp_codes(user):
    """
    Tests the removal of expired codes for account activation,
    email change, and password reset.
    """
    # Persists codes with expired dates
    code_data = {"user": user, "expires_at": timezone.now() - timedelta(days=1)}
    activation_code = AccountActivationCodeModel.objects.create(**code_data).code
    change_code = ChangeEmailCodeModel.objects.create(**code_data).code
    reset_code = ResetPasswordCodeModel.objects.create(**code_data).code

    # Verify if codes exist before removing them
    assert ChangeEmailCodeModel.objects.filter(code=change_code).exists()
    assert AccountActivationCodeModel.objects.filter(code=activation_code).exists()
    assert ResetPasswordCodeModel.objects.filter(code=reset_code).exists()

    # Call command to remove codes
    call_command("remove_exp_code")

    # Verify if the codes have been removed
    assert not ChangeEmailCodeModel.objects.filter(code=change_code).exists()
    assert not AccountActivationCodeModel.objects.filter(code=activation_code).exists()
    assert not ResetPasswordCodeModel.objects.filter(code=reset_code).exists()
