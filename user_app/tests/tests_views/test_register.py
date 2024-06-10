import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()

url: str = reverse("register")


@pytest.fixture
def client() -> APIClient:
    """Retorna um cliente de API para fazer solicitações."""
    return APIClient()


@pytest.fixture
def user_registration_data() -> dict[str:str]:
    """Retorna os dados de registro do usuário para a solicitação."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "johndoe@example.com",
        "password": "Password123!*",
        "confirmation_password": "Password123!*",
    }


@pytest.fixture
def expected_user_data() -> dict[str:str]:
    """Retorna os dados esperados do usuário no banco de dados após a criação."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "johndoe@example.com",
    }


@pytest.mark.django_db
def test_creates_user_with_valid_data(
    client: APIClient,
    user_registration_data: dict[str:str],
    expected_user_data: dict[str:str],
):
    """
    Testa se um novo usuário é criado corretamente com dados válidos.

    Args:
        client (APIClient): Cliente de API para fazer solicitações.
        user_registration_data (dict): Dados de registro do usuário para a solicitação.
        expected_user_data (dict): Dados esperados do usuário no banco de dados após a criação.
    """
    # Faz a solicitação POST para registrar o usuário
    response = client.post(url, data=user_registration_data, format="json")

    # Adiciona o ID do usuário criado aos dados esperados
    expected_user_data["id"] = response.data["user"]["id"]

    # Verifica se o usuário foi criado no banco de dados com os dados esperado
    assert User.objects.filter(**expected_user_data).exists()
    # Verifica o código de status da resposta
    assert status.HTTP_201_CREATED == response.status_code
    # Verifica a mensagem de sucesso na resposta
    assert "User registered successfully" == response.data["message"]


# Email vadalidaton
@pytest.mark.parametrize(
    "invalid_email_format",
    [
        "email.com",
        "email@@domain.com",
        ".email@domain.com",
        "email.@domain.com",
        "em..ail@domain.com",
        "e mail@domain.com",
        "@domain.com",
        "email@",
        "email@domain",
        "email@domain..com",
        "email@[domain.com]",
        "email@domain.",
    ],
)
@pytest.mark.django_db
def test_does_not_create_user_with_invalid_email_format(
    invalid_email_format, client: APIClient, user_registration_data: dict[str, str]
):
    """
    Testa se um usuário não é criado quando o email tem um formato inválido.

    Args:
        invalid_email_format (str): Formato inválido de email a ser testado.
        client (APIClient): Cliente de API para fazer solicitações.
        user_registration_data (dict): Dados de registro do usuário para a solicitação.
    """
    user_registration_data["email"] = invalid_email_format

    # Faz a solicitação POST para registrar o usuário
    response = client.post(url, data=user_registration_data, format="json")

    # Verifica se o código de status da resposta é 400 BAD REQUEST
    assert status.HTTP_400_BAD_REQUEST == response.status_code
    # Verifica se o campo 'email' está presente nos erros de validação
    assert "email" in response.data["validation_errors"]
    # Verifica a mensagem de erro.
    assert "Enter a valid email address." in response.data["validation_errors"]["email"]


@pytest.mark.django_db
def test_does_not_create_user_with_duplicate_email(
    client: APIClient, user_registration_data: dict[str, str]
):
    """
    Testa se um usuário não é criado quando o email já está registrado.

    Args:
        client (APIClient): Cliente de API para fazer solicitações.
        user_registration_data (dict): Dados de registro do usuário para a solicitação.
    """
    # Cria um usuário com o email fornecido
    client.post(url, data=user_registration_data, format="json")

    # Tenta criar um segundo usuário com o mesmo email
    response = client.post(url, data=user_registration_data, format="json")

    # Verifica se o código de status da resposta é 400 BAD REQUEST
    assert status.HTTP_400_BAD_REQUEST == response.status_code
    # Verifica se o campo 'email' está presente nos erros de validação
    assert "email" in response.data["validation_errors"]
    # Verifica a mensagem de erro.
    assert (
        "User Profile with this email already exists."
        in response.data["validation_errors"]["email"]
    )


@pytest.mark.django_db
def test_does_not_create_use_with_blank_email(
    client: APIClient, user_registration_data: dict[str, str]
):
    """Testa se o usuário não é criado quando a senha é blank.

    Args:
        client (APIClient): Cliente de API para fazer as solicitações.
        user_registration_data (dict[str, str]): Dados de registro do usuário para solicitação.
    """
    # Remove o campo email
    del user_registration_data["email"]

    # Faz a solicitação POST para registrar o usuário
    response = client.post(url, data=user_registration_data, format="json")

    # Verifica se o código de status da resposta é 400 BAD REQUEST
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    # Verifica se o campo 'email' está presente nos erros de validação
    assert "email" in response.data["validation_errors"]
    # Verifica se a mensagem de erro
    assert "This field is required." in response.data["validation_errors"]["email"]


@pytest.mark.django_db
def test_does_not_create_user_with_null_email(
    client: APIClient, user_registration_data: dict[str, str]
):
    """
    Testa se um usuário não é criado quando o email é nulo.

    Args:
        client (APIClient): Cliente de API para fazer solicitações.
        user_registration_data (dict): Dados de registro do usuário para a solicitação.
    """
    user_registration_data["email"] = None

    # Faz a solicitação POST para registrar o usuário
    response = client.post(url, data=user_registration_data, format="json")

    # Verifica se o código de status da resposta é 400 BAD REQUEST
    assert status.HTTP_400_BAD_REQUEST == response.status_code
    # Verifica se o campo 'email' está presente nos erros de validação
    assert "email" in response.data["validation_errors"]
    # Verifica a mensagem de erro.
    assert "This field may not be null." in response.data["validation_errors"]["email"]


# Password validation
@pytest.mark.django_db
def test_does_not_create_user_with_different_passwords(
    client: APIClient, user_registration_data: dict[str, str]
):
    """
    Testa se um usuário não é criado quando as senhas fornecidas são diferentes.

    Args:
        client (APIClient): Cliente de API para fazer solicitações.
        user_registration_data (dict): Dados de registro do usuário para a solicitação.
    """
    # Altera o campo 'confirmation_password' para uma senha diferente
    user_registration_data["confirmation_password"] = "DifferentPassword123!*"

    # Faz a solicitação POST para registrar o usuário
    response = client.post(url, data=user_registration_data, format="json")

    # Verifica se o código de status da resposta é 400 BAD REQUEST
    assert status.HTTP_400_BAD_REQUEST == response.status_code
    # Verifica se o campo 'confirmation_password' está presente nos erros de validação
    assert "confirmation_password" in response.data["validation_errors"]
    # Verifica a mensagem de erro.
    assert (
        "Passwords do not match"
        in response.data["validation_errors"]["confirmation_password"]
    )


@pytest.mark.django_db
def test_does_not_create_user_with_short_password(
    client: APIClient, user_registration_data: dict[str, str]
):
    """Testa se o usuário não é criado quando a senha fornecida é menor que 8 caracteres.

    Args:
        client (APIClient): Cliente de API para fazer as solicitações.
        user_registration_data (dict[str, str]): Dados de registro do usuário para solicitação.
    """

    # Altera o campo 'password' para uma senha menor que 8 caracteres.
    short_password = "abc!100"
    user_registration_data["password"] = short_password
    user_registration_data["confirmation_password"] = short_password

    # Faz a solicitação POST para registrar o usuário
    response = client.post(url, data=user_registration_data, format="json")

    # Verifica se o código de status da resposta é 400 BAD REQUEST
    assert status.HTTP_400_BAD_REQUEST == response.status_code
    # Verifica se o campo 'password' está presente nos erros de validação
    assert "password" in response.data["validation_errors"]
    # Verifica se a mensagem de erro
    assert (
        "This password is too short. It must contain at least 8 characters."
        in response.data["validation_errors"]["password"].__str__()
    )


@pytest.mark.django_db
def test_does_not_create_user_with_numeric_password(
    client: APIClient, user_registration_data: dict[str, str]
):
    """Testa se o usuário não é criado quando a senha é somente numérica.

    Args:
        client (APIClient): Cliente de API para fazer as solicitações.
        user_registration_data (dict[str, str]): Dados de registro do usuário para solicitação.
    """

    # Altera o campo 'password' para uma senha somente numérica
    numeric_password = "12345678910"
    user_registration_data["password"] = numeric_password
    user_registration_data["confirmation_password"] = numeric_password

    # Faz a solicitação POST para registrar o usuário
    response = client.post(url, data=user_registration_data, format="json")

    # Verifica se o código de status da resposta é 400 BAD REQUEST
    assert status.HTTP_400_BAD_REQUEST == response.status_code
    # Verifica se o campo 'password' está presente nos erros de validação
    assert "password" in response.data["validation_errors"]
    # Verifica se a mensagem de erro
    assert (
        "This password is entirely numeric."
        in response.data["validation_errors"]["password"].__str__()
    )


@pytest.mark.django_db
def test_does_not_create_user_with_common_password(
    client: APIClient, user_registration_data: dict[str, str]
):
    """Testa se o usuário não é criado quando a senha é comum.

    Args:
        client (APIClient): Cliente de API para fazer as solicitações.
        user_registration_data (dict[str, str]): Dados de registro do usuário para solicitação.
    """

    # Altera o campo 'password' para uma senha comum.
    numeric_password = "password123"
    user_registration_data["password"] = numeric_password
    user_registration_data["confirmation_password"] = numeric_password

    # Faz a solicitação POST para registrar o usuário
    response = client.post(url, data=user_registration_data, format="json")

    # Verifica se o código de status da resposta é 400 BAD REQUEST
    assert status.HTTP_400_BAD_REQUEST == response.status_code
    # Verifica se o campo 'password' está presente nos erros de validação
    assert "password" in response.data["validation_errors"]
    # Verifica se a mensagem de erro
    assert (
        "This password is too common."
        in response.data["validation_errors"]["password"].__str__()
    )


# first_name test


@pytest.mark.django_db
def test_does_not_create_user_with_blank_first_name(
    client: APIClient, user_registration_data: dict[str, str]
):
    """Testa se o usuário não é criado quando o first_name é blank.

    Args:
        client (APIClient): Cliente de API para fazer as solicitações.
        user_registration_data (dict[str, str]): Dados de registro do usuário para solicitação
    """
    # Altera o campo first_name para um valor vazio.
    user_registration_data["first_name"] = ""

    # Faz a solicitação POST para registrar o usuário
    response = client.post(url, data=user_registration_data, format="json")

    # Verifica se o código de status da resposta é 400 BAD REQUEST
    assert status.HTTP_400_BAD_REQUEST == response.status_code
    # Verifica se o campo 'first_name' está presente nos erros de validação
    assert "first_name" in response.data["validation_errors"]
    # Verifica se a mensagem de erro
    assert (
        "This field may not be blank."
        in response.data["validation_errors"]["first_name"]
    )


@pytest.mark.django_db
def test_does_not_create_user_with_null_first_name(
    client: APIClient, user_registration_data: dict[str, str]
):
    """Testa se o usuário não é criado quando o first_name é null.

    Args:
        client (APIClient): Cliente de API para fazer as solicitações.
        user_registration_data (dict[str, str]): Dados de registro do usuário para soilicitação.

    """
    # Altera o campo first_name para um valor None.
    user_registration_data["first_name"] = None

    response = client.post(url, data=user_registration_data, format="json")

    # Verifica se o código de status da resposta é 400 BAD REQUEST
    assert status.HTTP_400_BAD_REQUEST == response.status_code
    # Verifica se o campo 'first_name' está presente nos erros de validação
    assert "first_name" in response.data["validation_errors"]
    # Verifica se a mensagem de erro
    assert (
        "This field may not be null."
        in response.data["validation_errors"]["first_name"]
    )


@pytest.mark.django_db
def test_does_not_create_user_with_too_long_first_name(
    client: APIClient, user_registration_data: dict[str, str]
):
    """Testa se o usuário não é criado quando o first_name é muito longo.

    Args:
        client (APIClient): Cliente de API para fazer as solicitações.
        user_registration_data (dict[str, str]): Dados de registro do usuário para soilicitação.

    """
    # Altera o campo first_name para um valor com nome muito longo.
    user_registration_data["first_name"] = "my_name" * 15

    response = client.post(url, data=user_registration_data, format="json")

    # Verifica se o código de status da resposta é 400 BAD REQUEST
    assert status.HTTP_400_BAD_REQUEST == response.status_code
    # Verifica se o campo 'first_name' está presente nos erros de validação
    assert "first_name" in response.data["validation_errors"]
    # Verifica se a mensagem de erro
    assert (
        "Ensure this field has no more than 100 characters."
        in response.data["validation_errors"]["first_name"]
    )


@pytest.mark.django_db
def test_does_not_create_user_with_blank_last_name(
    client: APIClient, user_registration_data: dict[str, str]
):
    """Testa se o usuário não é criado quando o last_name é blank.

    Args:
        client (APIClient): Cliente de API para fazer as solicitações.
        user_registration_data (dict[str, str]): Dados de registro do usuário para solicitação
    """
    # Altera o campo last_name para um valor vazio.
    user_registration_data["last_name"] = ""

    # Faz a solicitação POST para registrar o usuário
    response = client.post(url, data=user_registration_data, format="json")

    # Verifica se o código de status da resposta é 400 BAD REQUEST
    assert status.HTTP_400_BAD_REQUEST == response.status_code
    # Verifica se o campo 'last_name' está presente nos erros de validação
    assert "last_name" in response.data["validation_errors"]
    # Verifica se a mensagem de erro
    assert (
        "This field may not be blank."
        in response.data["validation_errors"]["last_name"]
    )


@pytest.mark.django_db
def test_does_not_create_user_with_null_last_name(
    client: APIClient, user_registration_data: dict[str, str]
):
    """Testa se o usuário não é criado quando o last_name é null.

    Args:
        client (APIClient): Cliente de API para fazer as solicitações.
        user_registration_data (dict[str, str]): Dados de registro do usuário para soilicitação.

    """
    # Altera o campo last_name para um valor None.
    user_registration_data["last_name"] = None

    response = client.post(url, data=user_registration_data, format="json")

    # Verifica se o código de status da resposta é 400 BAD REQUEST
    assert status.HTTP_400_BAD_REQUEST == response.status_code
    # Verifica se o campo 'last_name' está presente nos erros de validação
    assert "last_name" in response.data["validation_errors"]
    # Verifica se a mensagem de erro
    assert (
        "This field may not be null." in response.data["validation_errors"]["last_name"]
    )


@pytest.mark.django_db
def test_does_not_create_user_with_too_long_last_name(
    client: APIClient, user_registration_data: dict[str, str]
):
    """Testa se o usuário não é criado quando o last_name é muito longo.

    Args:
        client (APIClient): Cliente de API para fazer as solicitações.
        user_registration_data (dict[str, str]): Dados de registro do usuário para soilicitação.

    """
    # Altera o campo last_name para um valor com nome muito longo.
    user_registration_data["last_name"] = "my_name" * 15

    response = client.post(url, data=user_registration_data, format="json")

    # Verifica se o código de status da resposta é 400 BAD REQUEST
    assert status.HTTP_400_BAD_REQUEST == response.status_code
    # Verifica se o campo 'last_name' está presente nos erros de validação
    assert "last_name" in response.data["validation_errors"]
    # Verifica se a mensagem de erro
    assert (
        "Ensure this field has no more than 100 characters."
        in response.data["validation_errors"]["last_name"]
    )
