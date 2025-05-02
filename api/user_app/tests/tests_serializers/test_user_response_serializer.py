import pytest
from user_app.serializers import AccountResponseSerializer
from user_app.tests.constants import Account


# ============== Fixtures  ======================
@pytest.fixture
def valid_account_data() -> dict[str, str]:
    """
    Returns valid data for a new account.
    """

    return {
        "email": "fake@email.com",
        "password": "1234_!Fake",
        "first_name": "fake_first_name",
        "last_name": "fake_last_name",
    }


@pytest.fixture
def account(valid_account_data: dict):
    return Account.objects.create_user(**valid_account_data)


# ============== Tests ==================
@pytest.mark.django_db
def test_should_return_the_correct_fields(account):
    serializer = AccountResponseSerializer(instance=account)

    assert account.id == serializer.data["id"]
    assert account.first_name == serializer.data["first_name"]
    assert account.last_name == serializer.data["last_name"]
    assert account.email == serializer.data["email"]
    assert account.is_active == serializer.data["is_active"]
    assert "password" not in serializer.data
