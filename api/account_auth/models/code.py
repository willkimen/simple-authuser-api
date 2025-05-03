"""
Module responsible for managing verification codes.

This module defines abstract and concrete models to store codes used in
account verification, password reset, and email change processes.
It also includes a manager that handles the generation and maintenance of these codes,
ensuring their uniqueness and validity.

The models are linked to accounts through their email addresses
and include fields to track code creation and expiration times.

This module is designed to be reusable across different verification flows in the system.
"""

from datetime import datetime, timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from account_auth.constants.verification_code import (
    ACTIVATE_ACCOUNT_PREFIX,
    CHANGE_EMAIL_PREFIX,
    CODE_EXPIRATION_HOURS,
    RESET_PASSWORD_PREFIX,
)
from account_auth.utils import generate_random_code


class VerificationCodeManager(models.Manager):
    def keep_latest_code(self, account_email: str) -> None:
        """
        Removes all verification codes for an account, except the most recent one.

        This method retrieves all records associated with the given account's email,
        ordered by the "created_at" field in descending order. It keeps the most
        recent record and deletes the rest.

        Args:
            account_email (str): The email of the account whose older codes should be removed.

        Returns:
            None
        """
        codes = self.model.objects.filter(account_id=account_email).order_by(
            "-created_at"
        )
        if codes.count() > 1:
            # Keep the latest code and delete the rest.
            codes.exclude(pk=codes.first().pk).delete()

    def verify_and_return_new_code(self, prefix: str) -> str:
        """
        Generates a unique verification code with the specified prefix.

        This method generates a new verification code using a provided prefix and
        ensures its uniqueness by verifying that it does not already exist
        in the database.
        If the generated code already exists, the method will generate another one until
        a unique code is found.

        Args:
            prefix (str): The prefix to use for the verification code.

        Returns:
            str: A unique verification code.
        """
        code: str = generate_random_code(prefix=prefix)
        while self.model.objects.filter(code=code).exists():
            code: str = generate_random_code(prefix=prefix)
        return code


class VerificationCodeBaseModel(models.Model):
    """
    Abstract model that will serve as a base for others.

    This model is used as a base class for models intended to store verification codes
    for various scenarios such as: account activation, email change
    and password reset (in case the account has forgotten their password).

    Fields:
    - `code` (CharField): The verification code. This field is required, must be unique,
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

    objects = VerificationCodeManager()
    _prefix = ""
    code = models.CharField(max_length=16, unique=True, null=False, blank=False)
    created_at = models.DateTimeField()
    expires_at = models.DateTimeField()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs) -> None:
        """
        This method was overridden so that if the account does not directly set fields
        such as created_at, expires_at and code, they are automatically set.
        """
        if not self.pk:
            if self.created_at is None:
                self.created_at: datetime = timezone.now()

            if self.expires_at is None:
                self.expires_at: datetime = self.created_at + timedelta(
                    hours=CODE_EXPIRATION_HOURS
                )

            if not self.code:
                self.code: str = generate_random_code(prefix=self._prefix)

        super().save(*args, **kwargs)


class AccountActivationCodeModel(VerificationCodeBaseModel):
    """
    Model for storing account activation codes.

    This model is used to store activation codes for verifying account accounts.
    It extends the `verificationCodeBaseModel` and includes additional fields
    specific to account activation.

    Fields:
    - account (ForeignKey): A foreign key relationship to the default account defined in
                         settings.AUTH_USER_MODEL, representing the account that owns
                         this token.


    How to relate the account to this model?:
        You can either pass an account instance to the .account=account_instance or
        the account's email to the .account_id=account_instance.email.
    """

    _prefix = ACTIVATE_ACCOUNT_PREFIX
    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=False,
        related_name="account_activation_codes",
        to_field="email",
        db_column="account_email",
    )

    class Meta:
        db_table = "account_activation_code"
        verbose_name = "account activation code"


class ChangeEmailCodeModel(VerificationCodeBaseModel):
    """
    Model for storing email change verification codes.

    This model stores codes used for changing an account's email address.
    It extends the `verificationCodeBaseModel` and includes additional fields for the
    actual and new email addresses.

    Fields:
    - account (ForeignKey): A foreign key relationship to the default account defined in
                         settings.AUTH_USER_MODEL, representing the account that owns
                         this token.

    - `new_email` (EmailField): The account's new email address. This field is required.

    How to relate the account to this model?:
        You can either pass an account instance to the .account=account_instance or
        the account's email to the .account_id=account_instance.email.
    """

    _prefix = CHANGE_EMAIL_PREFIX
    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=False,
        related_name="change_email_codes",
        to_field="email",
        db_column="old_account_email",
    )
    new_email = models.EmailField(unique=False, null=False, blank=False)

    class Meta:
        db_table = "change_email_code"
        verbose_name = "change email code"


class ResetPasswordCodeModel(VerificationCodeBaseModel):
    """
    Model for storing password reset verification codes.

    This model stores codes used for resetting an account's password.
    It extends the `VerificationCodeBaseModel` and is associated with the account
    via their email address.

    Fields:
    - account (ForeignKey): A foreign key relationship to the default account defined in
                         settings.AUTH_USER_MODEL, representing the account that owns
                         this token.

    How to relate the account to this model?:
        You can either pass an account instance to the .account=account_instance or
        the account's email to the .account=account_instance.email.
    """

    _prefix = RESET_PASSWORD_PREFIX
    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=False,
        related_name="reset_password_codes",
        to_field="email",
        db_column="account_email",
    )

    class Meta:
        db_table = "reset_password_code"
        verbose_name = "reset password code"
