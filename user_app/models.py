from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from .constants import confirmation_type_code


class UserProfileManager(BaseUserManager):
    """
    Custom user profile manager to handle the creation of
    regular users and superusers.
    """

    def create_user(self, email, password, is_active=False, **extra_fields):
        """Creates a regular user with with account not activated by default.

        Raises:
            ValueError: If the email address is not provided.
            ValueError: If the password is not provided.

        Returns:
            UserProfile: The created and persisted user in the database.
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
        """Creates a superuser

        Raises:
            ValueError: If the is_staff field is not True.
            ValueError: If the is_superuser field is not True.

        Returns:
            UserProfile: The created superuser.
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
    User profile model that replaces the 'username' field with 'email' for
    authentication.
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
    Model representing a confirmation code for various user actions.

    Attributes:
        TYPE_CODE_OPTIONS (list): List of tuples containing the available types of confirmation codes.

        user_email (EmailField): The email associated with the confirmation code.
        code (CharField): The unique confirmation code.
        created_at (DateTimeField): The date and time when the confirmation code was created.
        type_code (CharField): The type of confirmation code, chosen from TYPE_CODE_OPTIONS.
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
