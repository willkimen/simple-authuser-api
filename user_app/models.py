from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone

from user_app.constants import prefixes
from user_app.utils.random_code import generate_random_code


class UserProfileManager(BaseUserManager):
    """
    Custom manager for the UserProfileModel to handle user creation and management.

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
            UserProfileModel: The created user instance.
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
            UserProfileModel: The created superuser instance.
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


class UserProfileModel(AbstractUser):
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


class ConfirmationCodeBaseModel(models.Model):
    """
    Abstract base model for storing confirmation codes.

    This model is used as a base class for specific confirmation code models, providing shared fields and logic for creating and managing confirmation codes. It includes fields for storing the code, creation time, and expiration time.

    Fields:
    - `code` (CharField): The confirmation code. This field is required, must be unique, and has a maximum length of 16 characters.
    - `created_at` (DateTimeField): The timestamp when the code was created. It is automatically set to the current time if not provided.
    - `expires_at` (DateTimeField): The timestamp when the code expires. It is automatically set to 24 hours after `created_at` if not provided.

    Methods:
    - `save`: Overrides the default save method to set default values for `created_at`, `expires_at`, and `code` if they are not provided. The code is generated using a function that allows for a customizable prefix defined in the subclass.

    Notes:
    - This class is meant to be subclassed and should not be used directly.
    """

    prefix = ""
    code = models.CharField(
        max_length=16,
        unique=True,
        null=False,
        blank=False,
    )
    created_at = models.DateTimeField()
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.created_at is None:
                self.created_at = timezone.now()

            if self.expires_at is None:
                self.expires_at = self.created_at + timedelta(hours=24)

            if not self.code:
                self.code = generate_random_code(prefix=self.prefix)

        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class AccountActivationCodeModel(ConfirmationCodeBaseModel):
    """
    Model for storing account activation codes.

    This model is used to store activation codes for verifying user accounts. It extends the `ConfirmationCodeBaseModel` and includes additional fields specific to account activation.

    Fields:
    - `user_email` (EmailField): The email address of the user associated with the activation code. This field is required.

    Inherited Fields:
    - `code` (CharField): The activation code itself. Must be unique and is automatically generated if not provided.
    - `created_at` (DateTimeField): The timestamp when the activation code was created. Automatically set if not provided.
    - `expires_at` (DateTimeField): The timestamp when the activation code expires. Automatically set to 24 hours after creation if not provided.

    Methods:
    - `save`: Overrides the base `save` method to provide a default prefix "ACT-" for activation codes.
    """

    prefix = prefixes.ACTIVATE_ACCOUNT_PREFIX
    user = models.ForeignKey(
        "UserProfileModel",
        on_delete=models.CASCADE,
        null=False,
        related_name="account_activation_code",
        to_field="email",
        db_column="user_email",
    )

    class Meta:
        db_table = "account_activation_code"
        verbose_name = "account activation code"


class ChangeEmailCodeModel(ConfirmationCodeBaseModel):
    """
    Model for storing email change confirmation codes.

    This model stores codes used for changing a user's email address. It extends the `ConfirmationCodeBaseModel` and includes additional fields for the actual and new email addresses.

    Fields:
    - `actual_email` (EmailField): The user's current email address. This field is required.
    - `new_email` (EmailField): The user's new email address. This field is required.

    Inherited Fields:
    - `code` (CharField): The confirmation code. Must be unique and is automatically generated if not provided.
    - `created_at` (DateTimeField): The timestamp when the confirmation code was created. Automatically set if not provided.
    - `expires_at` (DateTimeField): The timestamp when the confirmation code expires. Automatically set to 24 hours after creation if not provided.

    Methods:
    - `save`: Overrides the base `save` method to provide a default prefix "CHE-" for email change codes.
    """

    prefix = prefixes.CHANGE_EMAIL_PREFIX
    actual_email = models.EmailField(unique=False, null=False, blank=False)
    new_email = models.EmailField(unique=False, null=False, blank=False)

    class Meta:
        db_table = "change_email_code"
        verbose_name = "change email code"


class JWTBlacklistModel(models.Model):
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
