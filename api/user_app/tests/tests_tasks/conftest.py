import pytest
from user_app.tests.constants import User


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
