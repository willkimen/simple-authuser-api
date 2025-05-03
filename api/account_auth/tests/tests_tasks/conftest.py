import pytest
from account_auth.tests.constants import Account


# ============== Fixtures  ======================
@pytest.fixture
def account():
    """
    Creates and returns a mock account object for testing purposes.
    """
    account_data = {
        "email": "fake@email.com",
        "password": "1234_!Fake",
        "first_name": "fake_first_name",
        "last_name": "fake_last_name",
    }

    return Account.objects.create_user(**account_data)
