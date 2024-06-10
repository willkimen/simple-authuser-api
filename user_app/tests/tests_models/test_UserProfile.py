import pytest
from django.db import IntegrityError

from user_app.models import UserProfile


@pytest.fixture
def user_data():
    """
    Retorna dados de usuário padrão para uso nos testes.

    Returns:
        dict: Dados do usuário.
    """

    return {
        "email": "user@email.com",
        "password": "1234",
        "first_name": "my_name",
        "last_name": "my_last_name",
    }


@pytest.mark.django_db
def test_creates_user_instance(user_data):
    """
    Testa se uma instância de usuário é criada corretamente com os dados fornecidos.

    Args:
        user_data (dict): Dados do usuário.
    """
    user_instance = UserProfile.objects.create_user(**user_data)

    assert user_instance.email == user_data["email"], "Email do usuário não coincide."
    assert user_instance.check_password(
        user_data["password"]
    ), "A senha do usuário não coincide."
    assert (
        user_instance.first_name == user_data["first_name"]
    ), "O primeiro nome do usuário não coincide."
    assert (
        user_instance.last_name == user_data["last_name"]
    ), "O sobrenome do usuário não coincide."
    assert not user_instance.is_staff, "Usuário não deve ser staff."
    assert not user_instance.is_superuser, "Usuário não deve ser superusuário."


@pytest.mark.django_db
def test_does_not_create_user_without_email(user_data):
    """
    Testa se um erro é levantado ao tentar criar um usuário sem email.

    Args:
        user_data (dict): Dados do usuário.
    """
    del user_data["email"]
    with pytest.raises(TypeError):
        UserProfile.objects.create_user(**user_data)


@pytest.mark.django_db
def test_normalizes_email_domain(user_data):
    """
    Testa se o domínio do email é normalizado para minúsculas.

    Args:
        user_data (dict): Dados do usuário.
    """
    user_data["email"] = "email@DOMAINUPPERCASE.com"
    user = UserProfile.objects.create_user(**user_data)

    assert (
        user.email.islower()
    ), "O domínio do email não foi normalizado para minúsculas."


@pytest.mark.django_db
def test_does_not_create_user_with_duplicate_email(user_data):
    """
    Testa se um erro de integridade é levantado ao tentar criar dois usuários com o mesmo email.

    Args:
        user_data (dict): Dados do usuário.
    """
    with pytest.raises(IntegrityError):
        UserProfile.objects.create_user(**user_data)
        UserProfile.objects.create_user(**user_data)


@pytest.mark.django_db
def test_does_not_create_user_without_password(user_data):
    """
    Testa se um erro é levantado ao tentar criar um usuário sem senha.

    Args:
        user_data (dict): Dados do usuário.
    """
    del user_data["password"]
    with pytest.raises(TypeError):
        UserProfile.objects.create_user(**user_data)


@pytest.mark.django_db
def test_creates_superuser(user_data):
    """
    Testa se uma instância de superusuário é criada corretamente com os dados fornecidos.

    Args:
        user_data (dict): Dados do usuário.
    """
    superuser = UserProfile.objects.create_superuser(**user_data)

    assert superuser.is_staff, "Superusuário deve ser staff."
    assert superuser.is_superuser, "Superusuário deve ser superusuário."
