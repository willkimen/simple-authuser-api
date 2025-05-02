from datetime import timedelta

import pytest
from django.utils import timezone
from user_app.tests.constants import Account


# ============== Fixtures ==================
@pytest.fixture
def activated_account():
    """
    Creates and returns a fake account to be used in tests.
    """
    return Account.objects.create_user(
        id=1,
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fake@email.com",
        password="FAKEpassword10!",
        is_active=True,
    )


@pytest.fixture
def payload(activated_account) -> dict:
    return {
        "uid": activated_account.id,
        "typ": "refresh",
        "jti": "fake_jti",
        "exp": int((timezone.now() + timedelta(seconds=60)).timestamp()),
    }
