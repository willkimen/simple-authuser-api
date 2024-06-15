from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserProfileManager(BaseUserManager):
    """
    Custom user profile manager to handle the creation of
    regular users and superusers.
    """

    def create_user(self, email, password, **extra_fields):
        """Creates a regular user

        Args:
            email (str): User's email.
            password (str): User's password.

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

        email = self.normalize_email(email)  # Normalize the email domain
        user = self.model(
            email=email, **extra_fields
        )  # Create the user instance with additional fields
        user.set_password(password)  # Set the raw password for hashing
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """Creates a superuser

        Args:
            email (str): User's email.
            password (str): User's password.

        Raises:
            ValueError: If the is_staff field is not True.
            ValueError: If the is_superuser field is not True.

        Returns:
            UserProfile: The created superuser.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if (
            extra_fields.get("is_staff") is not True
        ):  # Check if is_staff is set to True.
            raise ValueError("Superuser must have is_staff=True.")
        if (
            extra_fields.get("is_superuser") is not True
        ):  # Check if is_superuser is set to True.
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


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

    REQUIRED_FIELDS: list[str] = (
        []
    )  # List of required fields besides email and password (empty in this case)

    objects = UserProfileManager()  # Set the custom manager

    class Meta:
        db_table = "user_profile"
        verbose_name = "User Profile"
        verbose_name_plural = "Users Profile"
