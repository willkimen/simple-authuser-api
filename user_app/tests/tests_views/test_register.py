import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from user_app.models import UserProfile


url: str = reverse('register')


@pytest.fixture
def client() -> APIClient:
    """Retorna um cliente de API para fazer solicitações."""
    return APIClient()


@pytest.fixture
def user_registration_data() -> dict[str:str]:
    """Retorna os dados de registro do usuário para a solicitação."""
    return {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'johndoe@example.com',
        'password': 'Password123!*',
        'confirmation_password': 'Password123!*',
    }


@pytest.fixture
def expected_user_data() -> dict[str:str]:
    """Retorna os dados esperados do usuário no banco de dados após a criação."""
    return {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'johndoe@example.com',
    }


@pytest.mark.django_db
def test_creates_user_with_valid_data(client: APIClient,
                                      user_registration_data: dict[str:str],
                                      expected_user_data: dict[str:str]):
    """
    Testa se um novo usuário é criado corretamente com dados válidos.

    Args:
        client (APIClient): Cliente de API para fazer solicitações.
        user_registration_data (dict): Dados de registro do usuário para a solicitação.
        expected_user_data (dict): Dados esperados do usuário no banco de dados após a criação.
    """
    expected_message = 'User registered successfully'
    expected_code = status.HTTP_201_CREATED

    # Faz a solicitação POST para registrar o usuário
    response = client.post(url, data=user_registration_data, format='json')

    # Verifica se o usuário foi criado no banco de dados
    assert UserProfile.objects.filter(**expected_user_data).exists()
    # Verifica o código de status da resposta
    assert expected_code == response.status_code
    # Verifica a mensagem de sucesso na resposta
    assert expected_message == response.data['message']
    # Verifica se o ID do usuário na resposta corresponde ao usuário criado
    assert UserProfile.objects.get(email=user_registration_data['email']).id == response.data['user_id']
