from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.tokens import PasswordResetTokenGenerator


class UserActiveTokenGenerator(PasswordResetTokenGenerator):
    """
    Gera um token para verificar se um usuário está ativo.

    Este gerador de tokens é baseado na classe PasswordResetTokenGenerator,
    que será usada para especificamente, confirmação de cadastro do usuário.


    Métodos:
        _make_hash_value(user, timestamp):
            Gera o valor hash para o token utilizando o ID do usuário,
            timestamp, is_active e email.
    """

    def _make_hash_value(self, user: AbstractBaseUser, timestamp: int) -> str:
        """
        Cria o valor hash para o token.

        Args:
            user (AbstractBaseUser): A instância do usuário para o qual o token é gerado.
            timestamp (int): O timestamp atual.

        Returns:
            str: O valor hash gerado.
        """
        email_field = (
            user.get_email_field_name()
        )  # Obtém o nome do campo de email do usuário
        email = (
            getattr(user, email_field, "") or ""
        )  # Obtém o valor do email do usuário, ou uma string vazia se não houver email
        return f"{user.id}{timestamp}{user.is_active}{email}"  # Retorna o valor hash composto pelo ID, timestamp, is_active e email


# Instância do gerador de token de atividade do usuário
user_active_generate_token = UserActiveTokenGenerator()
