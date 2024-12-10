from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserProfileManager(BaseUserManager):
    """
    This manager provides methods for creating a regular user and a superuser,
    where the email is used as the username.
    """

    def create_user(self, email: str, password: str, is_active=False, **extra_fields):
        """
        Create a user of the UserProfileManager type, which is by default
        persisted as inactive.
        Fields like email and password are required, and if they are not provided,
        the method will raise a ValueError exception.
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
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields):
        """
        Creates and returns a superuser with the specified email and password.
        Fields like email and password are required, and if they are not provided,
        the method will raise a ValueError exception.
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
        user.save(using=self._db)
        return user


class UserProfileModel(AbstractUser):
    """
    Extends the built-in AbstractUser model to use 'email' instead of 'username' for
    authentication.

    This model replaces the default 'username' field with 'email' for user
    identification and authentication.
    It also defines additional user profile fields such as 'first_name' and
    'last_name'.

    Configuration:
        USERNAME_FIELD (str): Specifies that 'email' should be used as the unique
                              identifier for authentication.

        REQUIRED_FIELDS (list[str]): List of fields that are required when creating a superuser.
                                     This list is empty as 'email' is used for authentication.

        objects (UserProfileManager): Specifies a custom manager for this model to
                                      handle user-related queries.
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
