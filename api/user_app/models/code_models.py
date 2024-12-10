from datetime import datetime, timedelta

from django.conf import settings
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
    - user (ForeignKey): A foreign key relationship to the default user defined in
                         settings.AUTH_USER_MODEL, representing the user that owns
                         this token.


    How to relate the user to this model?:
        You can either pass a user instance to the .user=user_instance or
        the user's email to the .user_id=user_instance.email.
    """

    _prefix = prefixes.ACTIVATE_ACCOUNT_PREFIX
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
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
    - user (ForeignKey): A foreign key relationship to the default user defined in
                         settings.AUTH_USER_MODEL, representing the user that owns
                         this token.

    - `new_email` (EmailField): The user's new email address. This field is required.

    How to relate the user to this model?:
        You can either pass a user instance to the .user=user_instance or
        the user's email to the .user_id=user_instance.email.
    """

    _prefix = prefixes.CHANGE_EMAIL_PREFIX
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
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
    - user (ForeignKey): A foreign key relationship to the default user defined in
                         settings.AUTH_USER_MODEL, representing the user that owns
                         this token.

    How to relate the user to this model?:
        You can either pass a user instance to the .user=user_instance or
        the user's email to the .user_id=user_instance.email.
    """

    _prefix = prefixes.RESET_PASSWORD_PREFIX
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=False,
        related_name="reset_password_codes",
        to_field="email",
        db_column="user_email",
    )

    class Meta:
        db_table = "reset_password_code"
        verbose_name = "reset password code"
