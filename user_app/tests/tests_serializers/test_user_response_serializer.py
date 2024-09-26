import pytest
from django.contrib.auth import get_user_model

from user_app.serializers import UserResponseSerializer

# ========== Objects and constants ============
User = get_user_model()


# ============== Fixtures  ======================
@pytest.fixture
def valid_user_data() -> dict[str, str]:
    """
    Returns valid data for a new user.
    """

    return {
        "email": "fake@email.com",
        "password": "1234_!Fake",
        "first_name": "fake_first_name",
        "last_name": "fake_last_name",
    }


@pytest.fixture
def user(valid_user_data: dict) -> User:
    return User.objects.create_user(**valid_user_data)


# ============== Tests ==================
@pytest.mark.django_db
def test_should_return_the_correct_fields(user: User):
    serializer = UserResponseSerializer(instance=user)

    assert user.id == serializer.data["id"]
    assert user.first_name == serializer.data["first_name"]
    assert user.last_name == serializer.data["last_name"]
    assert user.email == serializer.data["email"]
    assert user.is_active == serializer.data["is_active"]
    assert "password" not in serializer.data
