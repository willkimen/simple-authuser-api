from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models, transaction
from django.utils import timezone
from django.utils.timezone import now


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

        REQUIRED_FIELDS (list[str]): List of fields that are required when
                                     creating a superuser. This list is empty as 'email'
                                     is used for authentication.

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


class PendingAccountsManager(models.Manager):
    def get_first_reminder_accounts_today(self) -> list[PendingAccountsModel]:
        """
        Returns the PendingAccountsModel instances for users who should receive
        their first reminder today.

        How it works:
            - Filters records where `first_reminder_at` matches today's date.
            - Returns the full list of matching PendingAccountsModel instances.
        """
        today = now().date()
        return list(self.select_related("user").filter(first_reminder_at__date=today))

    def get_second_reminder_accounts_today(self) -> list[PendingAccountsModel]:
        """
        Returns the PendingAccountsModel instances for users who should receive
        their second reminder today.

        How it works:
            - Filters records where `second_reminder_at` matches today's date.
            - Returns the full list of matching PendingAccountsModel instances.
        """
        today = now().date()
        return list(self.select_related("user").filter(second_reminder_at__date=today))

    def delete_expired_accounts(self) -> None:
        """
        Deletes users whose account activation period has expired.
        Saves their emails into the notification table before deletion.
        """
        # Filters PendingAccountsModel whose account activation period has expired.
        pending_accounts: list[PendingAccountsModel] = list(
            self.select_related("user").filter(
                activation_deadline__date__lt=timezone.now().date()
            )
        )

        if pending_accounts:
            with transaction.atomic():
                emails_to_persist = []
                user_ids_to_delete = []

                for pending_account in pending_accounts:
                    user = pending_account.user
                    emails_to_persist.append(
                        UsersPendingDeletionNotificationModel(email=user.email)
                    )
                    user_ids_to_delete.append(user.id)

                # Save emails from users who will be deleted for later notification.
                UsersPendingDeletionNotificationModel.objects.bulk_create(
                    emails_to_persist
                )

                # Delete users (automatic cascade in relationships)
                UserProfileModel.objects.filter(id__in=user_ids_to_delete).delete()


class PendingAccountsModel(models.Model):
    """
    Model that stores data about users who have not yet activated their accounts.

    This model:
        - Creates a one-to-many relationship with the user model.
        - Stores notification dates for account activation reminders.
        - Defines the final deadline for activation, after which the user's data
          will be permanently deleted.

    Fields:
        user (ForeignKey): A reference to the user who has not activated
                           their account.
        first_reminder_at (DateTimeField): The date and time of the first
                                           reminder email.
        second_reminder_at (DateTimeField): The date and time of the second
                                            reminder email.
        activation_deadline (DateTimeField): The final deadline for account activation.

    Constants:
        CUTOFF_HOUR:
            - Defines the hour that determines how the system calculates the first and
              second reminder dates.
            - When a user registers, their `date_joined` timestamp is recorded.
            - If the user registers before this hour, the current day is considered
              as "Day 1" of their pending activation period.
            - If the user registers at or after this hour, "Day 1" starts on the
              next day.

        REMINDER_DAYS:
            - A dictionary that defines how many days after registration the reminders
              are sent, depending on whether the user registered before or after
              `CUTOFF_HOUR`.

            - Example:
                REMINDER_DAYS = {
                    "before_cutoff":{"first_day": 1,"second_day": 4},
                    "after_cutoff":{"first_day": 2,"second_day": 5},
                }

            - "before_cutoff" applies when registration is before `CUTOFF_HOUR`.
            - "after_cutoff" applies when registration is at or after `CUTOFF_HOUR`.

    Usage:
        - This model is used to keep track of users who haven't activated their
          accounts yet.
        - The system will automatically send email reminders based
          on `first_reminder_at` and `second_reminder_at`.
        - If the user does not activate their account before `activation_deadline`,
          their data will be permanently removed.
    """

    CUTOFF_HOUR = 18
    REMINDER_DAYS = {
        "before_cutoff": {"first_day": 1, "second_day": 4},
        "after_cutoff": {"first_day": 2, "second_day": 5},
    }

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=False,
        related_name="pending_account",
    )
    first_reminder_at = models.DateTimeField(null=False, blank=False)
    second_reminder_at = models.DateTimeField(null=False, blank=False)
    activation_deadline = models.DateTimeField(null=False, blank=False)

    objects = PendingAccountsManager()

    class Meta:
        db_table = "pending_accounts"
        verbose_name = "Pending Accounts"

    def save(self, *args, **kwargs) -> None:
        """
        Automatically sets notification dates and the activation deadline before
        saving the instance to the database.

        How it works:
            - The `first_reminder_at` and `second_reminder_at` dates are calculated
              based on when the user registered (`date_joined`).

            - If the user registered on or after the time defined in `CUTOFF_HOUR`:

                - The first reminder will be scheduled for
                  `REMINDER_DAYS["after_cutoff"]["first_day"]`
                  days after registration.

                - The second reminder will be scheduled for
                  `REMINDER_DAYS["after_cutoff"]["second_day"]`
                  days after registration.

                - This happens because, in this case, "Day 1" of the activation period
                  starts the day after registration.

            - If the user registered before `CUTOFF_HOUR`:

                - The first reminder will be scheduled for
                  `REMINDER_DAYS["before_cutoff"]["first_day"]`
                  days after registration.

                - The second reminder will be scheduled for
                  `REMINDER_DAYS["before_cutoff"]["second_day"]`
                  days after registration.

                - This happens because, in this case, the registration day itself
                  is considered "Day 1" of the activation period.

            - The activation deadline (`activation_deadline`) is always set to the end
              of the day (23:59) when the second reminder is sent.

        Usage:
            - When persisting this model, the developer does not need* to manually
              set the reminder dates or the activation deadline.
            - But only the user instance needs to be provided:
                ```
                PendingAccountsModel.objects.create(user=user_instance)
                ```
                or
                ```
                PendingAccountsModel.objects.create(user_id=user_instance.id)
                ```
        """

        if self.user.date_joined.hour >= self.CUTOFF_HOUR:
            first_day = self.REMINDER_DAYS["after_cutoff"]["first_day"]
            second_day = self.REMINDER_DAYS["after_cutoff"]["second_day"]
        else:
            first_day = self.REMINDER_DAYS["before_cutoff"]["first_day"]
            second_day = self.REMINDER_DAYS["before_cutoff"]["second_day"]

        self.first_reminder_at = self.user.date_joined + timedelta(days=first_day)
        self.second_reminder_at = self.user.date_joined + timedelta(days=second_day)

        self.activation_deadline = self.second_reminder_at.replace(
            hour=23, minute=59, second=59, microsecond=0
        )

        super().save(*args, **kwargs)


class UsersPendingDeletionNotificationModel(models.Model):
    """
    Model to store emails of users who will be notified about their
    permanent account deletion.
    This model tracks users pending deletion and ensures that they are
    notified accordingly.

    Fields:
        email (EmailField): The unique email address of the user to notify.
    """

    email = models.EmailField(unique=True, null=False, blank=False)

    class Meta:
        db_table = "users_pending_deletion_notification"
