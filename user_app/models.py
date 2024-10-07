from datetime import datetime, timedelta

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone

from user_app.constants import prefixes
from user_app.utils.random_code import generate_random_code

""" 
Insert an integer representing the number of hours to define the expiration
time for the confirmation code, which will be used for various cases:
user account activation, password change, and password reset.
"""
EXPIRATION_TIME_IN_HOURS = 24


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


class ConfirmationCodeBaseModel(models.Model):
    """
    Abstract model that will serve as a base for others.

    This model is used as a base class for models intended to store confirmation codes
    for various scenarios such as: account activation, email change, password change,
    and password reset (in case the user has forgotten their password).

    Fields:
    - `code` (CharField): The confirmation code. This field is required, must be unique,
                          and has a maximum length of 16 characters.

    - `created_at` (DateTimeField): The timestamp when the code was created.
                                    It is automatically set to the current time if
                                    not provided.

    - `expires_at` (DateTimeField): The timestamp when the code expires.

    Methods:
    - `save`: Overrides the default save method to set default values for `created_at`,
              `expires_at`, and `code` if they are not provided. The code is generated
              using a function that allows for a customizable prefix defined
              in the subclass.

    Notes:
    - This class is meant to be subclassed and should not be used directly.
    - The class attribute __prefix is private and should not be set.
    """

    _prefix = ""
    code = models.CharField(max_length=16, unique=True, null=False, blank=False)
    created_at = models.DateTimeField()
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        """
        This method was overridden so that if the user does not directly set fields
        such as created_at, expires_at and code, they are automatically set.
        """
        if not self.pk:
            if self.created_at is None:
                self.created_at: datetime = timezone.now()

            if self.expires_at is None:
                self.expires_at: datetime = self.created_at + timedelta(
                    hours=EXPIRATION_TIME_IN_HOURS
                )

            if not self.code:
                self.code: str = generate_random_code(prefix=self._prefix)

        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class AccountActivationCodeModel(ConfirmationCodeBaseModel):
    """
    Model for storing account activation codes.

    This model is used to store activation codes for verifying user accounts.
    It extends the `ConfirmationCodeBaseModel` and includes additional fields
    specific to account activation.

    Fields:
    - `user` (ForeingKey): Foreign key that relates to the custom user
                           model UserProfileModel. The value of this field is not
                           the primary key, but the user's email.


    How to relate the user to this model?:
        You can either pass a user instance to the .user=user_instance or
        the user's email to the .user_id=user_instance.email.
    """

    _prefix = prefixes.ACTIVATE_ACCOUNT_PREFIX
    user = models.ForeignKey(
        "UserProfileModel",
        on_delete=models.CASCADE,
        null=False,
        related_name="account_activation_codes",
        to_field="email",
        db_column="user_email",
    )

    class Meta:
        db_table = "account_activation_code"
        verbose_name = "account activation code"


class ChangeEmailCodeModel(ConfirmationCodeBaseModel):
    """
    Model for storing email change confirmation codes.

    This model stores codes used for changing a user's email address.
    It extends the `ConfirmationCodeBaseModel` and includes additional fields for the
    actual and new email addresses.

    Fields:
    - `user` (ForeingKey): Foreign key that relates to the custom user
                           model UserProfileModel. The value of this field is not
                           the primary key, but the user's email.

    - `new_email` (EmailField): The user's new email address. This field is required.

    How to relate the user to this model?:
        You can either pass a user instance to the .user=user_instance or
        the user's email to the .user_id=user_instance.email.
    """

    _prefix = prefixes.CHANGE_EMAIL_PREFIX
    user = models.ForeignKey(
        "UserProfileModel",
        on_delete=models.CASCADE,
        null=False,
        related_name="change_email_codes",
        to_field="email",
        db_column="old_user_email",
    )
    new_email = models.EmailField(unique=False, null=False, blank=False)

    class Meta:
        db_table = "change_email_code"
        verbose_name = "change email code"


class ResetPasswordCodeModel(ConfirmationCodeBaseModel):
    """
    Model for storing password reset confirmation codes.

    This model stores codes used for resetting a user's password.
    It extends the `ConfirmationCodeBaseModel` and is associated with the user
    via their email address.

    Fields:
    - `user` (ForeignKey): Foreign key that relates to the custom user
                           model UserProfileModel. The value of this field is
                           the user's email, not the primary key.

    How to relate the user to this model?:
        You can either pass a user instance to the .user=user_instance or
        the user's email to the .user_id=user_instance.email.
    """

    _prefix = prefixes.RESET_PASSWORD_PREFIX
    user = models.ForeignKey(
        "UserProfileModel",
        on_delete=models.CASCADE,
        null=False,
        related_name="reset_password_codes",
        to_field="email",
        db_column="user_email",
    )

    class Meta:
        db_table = "reset_password_code"
        verbose_name = "reset password code"


class TokenModel(models.Model):
    """
    Abstract base model representing a JWT token.

    This model stores the `jti` (JWT ID) and `exp` (expiration time) of a token.
    The expiration field is managed to ensure it's stored as a `DateTimeField`,
    converting from an integer timestamp if necessary.


    Attributes:
        TYPE_TOKEN_CHOICES (list): Choices for the type of token.

        typ (CharField): The type of the token, which can be
                         either 'access' or 'refresh'. This field is limited
                         to the choices defined in `TYPE_TOKEN_CHOICES`.
    Methods:
        save: Overrides the default save method to handle the `exp` field conversion.
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

        If the expiration field (`exp`) is provided as an integer timestamp,
        it is converted to a datetime object before saving to the database.
        This ensures that the expiration time is correctly stored as a `DateTimeField`.

        Calls the parent class's save method to perform the actual save operation.
        """
        if isinstance(self.exp, int):
            self.exp: datetime = timezone.make_aware(datetime.fromtimestamp(self.exp))
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class BlacklistTokenModel(TokenModel):
    """
    Represents a model for storing blacklisted JWTs (JSON Web Tokens).
    This is used to keep track of tokens
    that should no longer be accepted by the system.

    Attributes:
        user (ForeignKey): A foreign key relationship to the `UserProfileModel`,
                           representing the user that owns this token.
    """

    user = models.ForeignKey(
        "UserProfileModel",
        on_delete=models.CASCADE,
        null=False,
        related_name="blacklist_tokens",
        db_column="uid",
    )

    class Meta:
        db_table = "blacklist_token"
        verbose_name = "blacklist token"


class ValidTokenModel(TokenModel):
    """
    Represents a model for storing valid tokens.

    Attributes:
        user (ForeignKey): A foreign key relationship to the `UserProfileModel`,
                           representing the user that owns this token.
    """

    user = models.ForeignKey(
        "UserProfileModel",
        on_delete=models.CASCADE,
        null=False,
        related_name="valid_tokens",
        db_column="uid",
    )

    class Meta:
        db_table = "valid_token"
        verbose_name = "valid token"
