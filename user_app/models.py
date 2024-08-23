from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from .constants import confirmation_type_code


class UserProfileManager(BaseUserManager):
    """
    Custom manager for the UserProfile model to handle user creation and management.

    This manager provides methods for creating regular users and superusers with proper
    validation and configuration.

    Methods:
        create_user(email, password, is_active=False, **extra_fields):
            Creates a regular user with the given email and password.

        create_superuser(email, password, **extra_fields):
            Creates a superuser with the given email and password.
    """

    def create_user(self, email, password, is_active=False, **extra_fields):
        """
        Creates and returns a regular user with the specified email and password.

        Args:
            email (str): The email address for the user.
            password (str): The password for the user.
            is_active (bool, optional): Specifies whether the user account is active. Defaults to False.
            **extra_fields: Additional fields for the user.

        Raises:
            ValueError: If the email or password is not provided.

        Returns:
            UserProfile: The created user instance.
        """
        if not email:
            raise ValueError("The email address must be entered")

        if not password:
            raise ValueError("The password must be entered")

        # Normalize the email domain
        email = self.normalize_email(email)
        # Create the user instance with additional fields
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.is_active = is_active
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Creates and returns a superuser with the specified email and password.

        Args:
            email (str): The email address for the superuser.
            password (str): The password for the superuser.
            **extra_fields: Additional fields for the superuser.

        Raises:
            ValueError: If the is_staff or is_superuser fields are not set to True.

        Returns:
            UserProfile: The created superuser instance.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        # Check if is_staff is set to True.
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        # Check if is_superuser is set to True.
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        user = self.create_user(email, password, **extra_fields)
        user.is_active = True
        user.save()
        return user


class UserProfile(AbstractUser):
    """
    Extends the built-in AbstractUser model to use 'email' instead of 'username' for authentication.

    This model replaces the default 'username' field with 'email' for user identification and authentication.
    It also defines additional user profile fields such as 'first_name' and 'last_name'.

    Attributes:
        username (NoneType): This field is set to None to remove the 'username' field inherited from AbstractUser.

        first_name (CharField): Stores the user's first name. This field is required.

        last_name (CharField): Stores the user's last name. This field is required.

        email (EmailField): Stores the user's email address. This field is unique and required.

    Configuration:
        USERNAME_FIELD (str): Specifies that 'email' should be used as the unique identifier for authentication.

        REQUIRED_FIELDS (list[str]): List of fields that are required when creating a superuser. This list is empty
                                      as 'email' is used for authentication.

        objects (UserProfileManager): Specifies a custom manager for this model to handle user-related queries.
    """

    username = None  # Remove the username field
    first_name = models.CharField(max_length=100, blank=False, null=False)
    last_name = models.CharField(max_length=100, blank=False, null=False)
    email = models.EmailField(unique=True, null=False, blank=False)

    USERNAME_FIELD = "email"  # Set email as the field used for authentication

    # List of required fields besides email and password (empty in this case)
    REQUIRED_FIELDS: list[str] = []

    objects = UserProfileManager()  # Set the custom manager

    class Meta:
        db_table = "user_profile"
        verbose_name = "User Profile"
        verbose_name_plural = "Users Profile"


class ConfirmationCode(models.Model):
    """
    Represents a confirmation code used for various user actions, such as account activation, email changes,
    password changes, and password resets.

    Attributes:
        TYPE_CODE_OPTIONS (list): List of tuples specifying the types of confirmation codes available.

        user_email (EmailField): The email address associated with this confirmation code. It is not unique,
                                  meaning multiple codes can be associated with the same email address.

        code (CharField): The unique confirmation code itself. It must be unique across all records.

        created_at (DateTimeField): The timestamp when the confirmation code was created. This field is automatically
                                    set to the current date and time when the record is created.

        type_code (CharField): The type of confirmation code, chosen from `TYPE_CODE_OPTIONS`. This indicates
                               the purpose of the confirmation code, such as account activation or password reset.
    """

    TYPE_CODE_OPTIONS = [
        (
            confirmation_type_code.ACCOUNT_ACTIVATION,
            "Registration Email Confirmation to account activation",
        ),
        (confirmation_type_code.EMAIL_CHANGE, "Email Change Confirmation"),
        (
            confirmation_type_code.PASSWORD_CHANGE,
            "Password Change Confirmation",
        ),
        (
            confirmation_type_code.PASSWORD_RESET,
            "Password Reset Confirmation",
        ),
    ]

    user_email = models.EmailField(unique=False, null=False, blank=False)
    code = models.CharField(max_length=32, unique=True, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    type_code = models.CharField(
        max_length=64, unique=False, null=False, blank=False, choices=TYPE_CODE_OPTIONS
    )

    class Meta:
        db_table = "confirmation_code"
        verbose_name = "Confirmation Code"


class JWTBlackList(models.Model):
    """
    Represents a model for storing blacklisted JWTs (JSON Web Tokens). This is used to keep track of tokens
    that should no longer be accepted by the system.

    Attributes:
        TYPE_TOKEN_CHOICES (list): Choices for the type of token.

        jti (CharField): The JWT ID (Unique Identifier). This field stores the unique identifier for the JWT.

        exp (DateTimeField): The expiration date and time of the token. This field indicates when the token expires.

        typ (CharField): The type of the token, which can be either 'access' or 'refresh'. This field is limited
                         to the choices defined in `TYPE_TOKEN_CHOICES`.
    """

    TYPE_TOKEN_CHOICES = [
        ("access", "access"),
        ("refresh", "refresh"),
    ]

    jti = models.CharField(max_length=255)
    exp = models.DateTimeField()
    typ = models.CharField(max_length=10, choices=TYPE_TOKEN_CHOICES)

    def save(self, *args, **kwargs):
        """
        Override the default save method to handle the expiration field.

        If the expiration field (`exp`) is provided as an integer timestamp, it is converted to a datetime object
        before saving to the database. This ensures that the expiration time is correctly stored as a `DateTimeField`.

        Args:
            *args: Variable length argument list.
            **kwargs: Keyworded variable length argument list.

        Calls the parent class's save method to perform the actual save operation.
        """
        if isinstance(self.exp, int):
            self.exp = datetime.fromtimestamp(self.exp, tz=ZoneInfo(settings.TIME_ZONE))
        super().save(*args, **kwargs)
