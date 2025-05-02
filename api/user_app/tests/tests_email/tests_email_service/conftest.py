import pytest
from user_app.tests.constants import Account


@pytest.fixture
def deactivated_account():
    """
    Fixture to create and return a deactivated Account object.
    """
    return Account.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fakeemail@email.com",
        password="FAKEpassword10!",
    )
