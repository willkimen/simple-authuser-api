import pytest
from django.contrib.auth import get_user_model  # type: ignore
from rest_framework.exceptions import ErrorDetail  # type: ignore

from user_app.serializers import UserSerializer

User = get_user_model()


# Fixtures para fornecer dados de teste
@pytest.fixture
def user_with_valid_fields():
    """
    Retorna dados válidos para um novo usuário.
    """
    return {
        "email": "user@email.com",
        "password": "1234_!pass",
        "confirmation_password": "1234_!pass",
        "first_name": "my_name",
        "last_name": "my_last_name",
    }


@pytest.fixture
def user_with_differents_passwords():
    """
    Retorna dados de usuário onde as senhas não coincidem.
    """
    return {
        "email": "user@email.com",
        "password": "1234_!pass",
        "confirmation_password": "1234_!pass_unmatched",
        "first_name": "my_name",
        "last_name": "my_last_name",
    }


@pytest.fixture
def user_with_invalid_passwords():
    """
    Retorna dados de usuário com uma senha inválida.
    """
    return {
        "email": "user@email.com",
        "password": "1234",
        "confirmation_password": "1234",
        "first_name": "my_name",
        "last_name": "my_last_name",
    }


@pytest.mark.django_db
def test_invalid_when_passwords_differ(user_with_differents_passwords: dict):
    """
    Testa se um erro é levantado quando as senhas não coincidem.

    Args:
        user_with_differents_passwords (dict): Dados de usuário onde as senhas não coincidem.
    """
    expected_error_message = "Passwords do not match"

    # Inicializa o serializer com os dados do usuário
    serializer = UserSerializer(data=user_with_differents_passwords)

    # Verifica se o serializer é inválido e se a mensagem de erro é a esperada
    assert (
        not serializer.is_valid()
    ), "Serializer deve ser inválido quando as senhas não coincidem."

    # Obtém o objeto ErrorDetail, que contém a mensagem de erro para o campo confirmation_password
    error_detail_field: ErrorDetail = serializer.errors.get(
        "confirmation_password", []
    )[0]

    # Obtém a mensagem do ErrorDetail
    error_detail_message: str = error_detail_field.__str__()

    assert (
        expected_error_message == error_detail_message
    ), f"Mensagem de erro inesperada: {error_detail_message}"


@pytest.mark.django_db
def test_user_persistence(user_with_valid_fields: dict):
    """
    Testa se um usuário com dados válidos é criado co

    Args:
        user_with_valid_fields (dict): Dados válidos para um novo usuário.rretamente no banco de dados.
    """
    # Inicializa o serializer com os dados do usuário
    serializer = UserSerializer(data=user_with_valid_fields)

    # Verifica se o serializer é válido e se o usuário foi persistido no banco de dados
    assert serializer.is_valid(), "Serializer deve ser válido para dados válidos."
    assert User.objects.filter(
        id=serializer.save().id
    ).exists(), "Usuário não foi persistido no banco de dados."


@pytest.mark.django_db
def test_confirmation_password_not_persisted(user_with_valid_fields: dict):
    """
    Testa se o campo 'confirmation_password' não é persi

    Args:
        user_with_valid_fields (dict): Dados válidos para um novo usuário.stido no modelo de usuário.
    """
    # Inicializa o serializer com os dados do usuário
    serializer = UserSerializer(data=user_with_valid_fields)

    # Verifica se o serializer é válido e se o campo 'confirmation_password' não está presente no objeto salvo
    assert serializer.is_valid(), "Serializer deve ser válido para dados válidos."
    assert not hasattr(
        serializer.save(), "confirmation_password"
    ), "Campo 'confirmation_password' não deve ser persistido, porém foi."


@pytest.mark.django_db
def test_invalid_password_validation(user_with_invalid_passwords):
    """
    Testa se a validação de senha inválida retorna os erros esperados.

    Args:
        user_with_invalid_passwords (dict): Dados de usuário com uma senha inválida.
    """
    expected_error_messages: list[str] = [
        "This password is too short. It must contain at least 8 characters.",
        "This password is too common.",
        "This password is entirely numeric.",
    ]

    # Inicializa o serializer com os dados do usuário
    serializer = UserSerializer(data=user_with_invalid_passwords)

    # Verifica se o serializer é inválido
    assert (
        not serializer.is_valid()
    ), "Serializer deve ser inválido para senhas inválidas."

    # Obtém o primeiro erro do campo 'password'
    error_detail_field: ErrorDetail = serializer.errors.get("password", [])[0]
    # Obtém a mensagem
    error_detail_message: str = error_detail_field.__str__()

    # Converte a mensagem de erro para uma lista de strings
    errors_messages: list[str] = eval(error_detail_message)

    # Verifica se as mensagens de erro são as esperadas
    expected_error_messages == errors_messages, f"Mensagens de erro inesperadas: {errors_messages}"
