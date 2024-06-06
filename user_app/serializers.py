from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers

from .models import UserProfile

# Obtém o modelo de usuário personalizado
User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer para registro de novos usuários. Valida e cria um novo usuário no sistema.
    """

    # Campo para confirmar a senha
    confirmation_password = serializers.CharField()

    class Meta:
        model = UserProfile
        # Campos incluídos no serializer
        fields = [
            "first_name",
            "last_name",
            "email",
            "password",
            "confirmation_password",
        ]
        # Define campos como write_only para que não sejam exibidos nas respostas
        extra_kwargs = {
            "password": {"write_only": True},
            "confirmation_password": {"write_only": True},
        }

    def create(self, validated_data):
        """
        Cria e retorna um novo usuário após a validação dos dados.

        Args:
            validated_data (dict): Dados validados do novo usuário.

        Returns:
            UserProfile: O usuário criado.
        """
        # Remove o campo password_confirmation dos dados validados
        validated_data.pop("confirmation_password", None)
        # Cria o usuário com os dados fornecidos
        return User.objects.create_user(**validated_data)

    def validate(self, data):
        """
        Valida os dados fornecidos durante o registro.

        Args:
            data (dict): Dados fornecidos para validação.

        Raises:
            serializers.ValidationError: Se as senhas não coincidirem.

        Returns:
            dict: Dados validados.
        """
        # Verifica se a senha e a confirmação de senha coincidem
        if data.get("password") != data.get("confirmation_password"):
            raise serializers.ValidationError(
                detail={"confirmation_password": "Passwords do not match"}
            )
        return data

    def validate_password(self, password):
        """
        Valida a força da senha utilizando as validações padrão do Django.

        Args:
            password (str): Senha a ser validada.

        Raises:
            serializers.ValidationError: Se a senha não atender aos requisitos de validação.

        Returns:
            str: A senha validada.
        """
        try:
            # Utiliza a validação padrão de senha do Django
            validate_password(password)
        except ValidationError as e:
            # Levanta um erro de validação com os detalhes do erro
            raise serializers.ValidationError(detail=e)
        return password
