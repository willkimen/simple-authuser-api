import pytest
from django.contrib.auth import get_user_model

from user_app.utils.token import user_active_generate_token

User = get_user_model()


@pytest.fixture
def user_instance() -> User:
    return User.objects.create_user(
        first_name="John",
        last_name="Doe",
        email="johndoe@example.com",
        password="Password123!*",
        is_active=False,
    )


@pytest.mark.django_db
def test_valid_token_when_data_user_does_not_change(user_instance: User):
    token = user_active_generate_token.make_token(user_instance)
    assert user_active_generate_token.check_token(user_instance, token)


@pytest.mark.django_db
def test_invalid_token_when_email_changes(user_instance: User):
    token = user_active_generate_token.make_token(user_instance)
    user_instance.email = "otheemail@email.com"
    assert not user_active_generate_token.check_token(user_instance, token)


@pytest.mark.django_db
def test_invalid_token_when_user_id_changes(user_instance: User):
    token = user_active_generate_token.make_token(user_instance)
    user_instance.id = user_instance.id + 1
    assert not user_active_generate_token.check_token(user_instance, token)


@pytest.mark.django_db
def test_invalid_token_when_is_active_changes(user_instance: User):
    token = user_active_generate_token.make_token(user_instance)
    user_instance.is_active = True
    assert not user_active_generate_token.check_token(user_instance, token)
