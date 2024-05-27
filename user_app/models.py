from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserProfileManager(BaseUserManager):
    """
    Gerenciador de perfil de usuário personalizado para manipular a criação de
    usuário comum e o super usuário.
    """

    def create_user(self, email, password, **extra_fields):
        """Cria um usuário comum

        Args:
            email (str): Email do usuário,
            password (str): Senha do usuário.

        Raises:
            ValueError: Se o endereço de email não for fornecido.
            ValueError: Se a senha não for fornecida.

        Returns:
            UserProfile: O usuário criado e persistido no base de dados
        """
        if not email:
            raise ValueError("The email address must be entered")

        if not password:
            raise ValueError("The password address must be entered")

        email = self.normalize_email(email)  # Normaliza o domínio do email
        user = self.model(email=email, **extra_fields)  # Cria a instância do usuário com os campos adicionais
        user.set_password(password)  # Seta a senha no formato raw para hash
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """Cria o superuser

        Args:
            email (str): Email do usuário.
            password (str): Senha do usuário.

        Raises:
            ValueError: Se o campo is_staff não for True.
            ValueError: Se o o campo is_superuser não for True.

        Returns:
            UserProfile: Usuário criado como superuser.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:  # Verifica se is_staff está definida como True.
            raise ValueError("Superuser must have is_staff=True.") 
        if extra_fields.get("is_superuser") is not True:  # Verifica se is_superuser está definida como True.
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class UserProfile(AbstractUser):
    """
    Modelo de perfil de usuário que substitui o campo 'username' pelo campo 'email' para
    a autenticação.
    """
    username = None  # Remove o campo username
    first_name = models.CharField(max_length=100, blank=False, null=False)
    last_name = models.CharField(max_length=100, blank=False, null=False)
    email = models.EmailField(unique=True, null=False, blank=False)

    USERNAME_FIELD = "email"  # Define o email como o campo utilizado para autenticação

    REQUIRED_FIELDS: list[str] = []  # Lista de campos obrigatórios além do email e senha (vazia neste caso)

    objects = UserProfileManager()   # Define o gerenciador personalizado

    class Meta:
        db_table = "user_profile"
        verbose_name = "User Profile"
        verbose_name_plural = "Users Profile"
