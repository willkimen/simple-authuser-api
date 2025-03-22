import pytest
from user_app.tests.constants import User


@pytest.fixture
def deactivated_user():
    """
    Fixture to create and return a deactivated User object.
    """
    return User.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fakeemail@email.com",
        password="FAKEpassword10!",
    )
