from datetime import timedelta

import pytest
import time_machine
from django.utils import timezone
from user_app.models import UserProfileModel
from user_app.models.user_models import (
    PendingAccountsModel,
    UsersPendingDeletionNotificationModel,
)

# ========== Constants ==================
USER_DATA = {
    "first_name": "Fake Name",
    "last_name": "Fake Last",
    "email": "fake@email.com",
    "is_active": False,
    "password": "FAKEfake123!",
}

EMAILS_INACTIVE_USERS = [
    "fake1@email.com",
    "fake2@email.com",
    "fake3@email.com",
]

# Sets today's date and a time before the cutoff hour.
TODAY_BEFORE_CUTOFF = timezone.now().replace(
    hour=(PendingAccountsModel.CUTOFF_HOUR - 1), minute=00, second=0, microsecond=0
)

# Set today's date and time exactly at the cutoff hour.
TODAY_CUTOFF = timezone.now().replace(
    hour=PendingAccountsModel.CUTOFF_HOUR, minute=00, second=0, microsecond=0
)

# Set the date of the first reminder
FIRST_REMINDER_DAY = timezone.now() + timedelta(
    days=PendingAccountsModel.REMINDER_DAYS["before_cutoff"]["first_day"]
)

# Set the date for the second reminder
SECOND_REMINDER_DAY = timezone.now() + timedelta(
    days=PendingAccountsModel.REMINDER_DAYS["before_cutoff"]["second_day"]
)

# Sets the deadline date for account activation.
ACTIVATION_DEADLINE_DAY = SECOND_REMINDER_DAY.replace(
    hour=23, minute=59, second=59, microsecond=0
)

DAY_AFTER_ACTIVATION_DEADLINE = ACTIVATION_DEADLINE_DAY + timedelta(seconds=1)


# ============ Fixtures =========================
@pytest.fixture
def user_registered_before_cutoff_hour():
    """
    Persist a registered user before the .CUTOFF_HOUR.
    """
    with time_machine.travel(TODAY_BEFORE_CUTOFF):
        return UserProfileModel.objects.create_user(**USER_DATA)


@pytest.fixture
def user_registered_at_cutoff_hour():
    """
    Persist a registered user at the .CUTOFF_HOUR.
    """
    with time_machine.travel(TODAY_CUTOFF):
        return UserProfileModel.objects.create_user(**USER_DATA)


@pytest.fixture
def create_users_for_reminder():
    """
    Fixture that creates unactivated users and associates
    them with PendingAccountsModel.

    This fixture:
        - Creates multiple users who registered before the cutoff hour defined
          by `CUTOFF_HOUR`.
        - Associates each user with a PendingAccountsModel instance to represent
          that their accounts are pending activation.
        - Simulates the registration time using time travel to ensure correct
          timestamps for reminder logic.
    """
    with time_machine.travel(TODAY_BEFORE_CUTOFF):
        for email in EMAILS_INACTIVE_USERS:
            USER_DATA["email"] = email
            user = UserProfileModel.objects.create_user(**USER_DATA)
            PendingAccountsModel.objects.create(user=user)


# ============== Tests ==================
@pytest.mark.django_db
def test_reminders_and_deadline_are_set_correctly_when_user_registers_before_cutoff_hour(
    user_registered_before_cutoff_hour,
):
    """
    Checks if the reminder dates and activation deadline are correctly set when a
    user registers before the time defined in `CUTOFF_HOUR`.

    Scenario:
        - A user registers before the cutoff time (`CUTOFF_HOUR`).
        - As a result, reminders should be scheduled considering that "Day 1" of
          the activation period starts on the registration day itself.
    Note:
        - This test ensures that the logic for setting dates is working correctly
          for users registered before the cutoff hour.
    """

    actual_pending = PendingAccountsModel.objects.create(
        user=user_registered_before_cutoff_hour
    )

    assert actual_pending.first_reminder_at.day == FIRST_REMINDER_DAY.day
    assert actual_pending.second_reminder_at.day == SECOND_REMINDER_DAY.day
    assert actual_pending.activation_deadline == ACTIVATION_DEADLINE_DAY


@pytest.mark.django_db
def test_reminders_and_deadline_are_set_correctly_when_user_registers_after_cutoff_hour(
    user_registered_at_cutoff_hour,
):
    """
    Checks if the reminder dates and activation deadline are correctly set when a
    user registers at or after `CUTOFF_HOUR`.

    Scenario:
        - A user registers exactly at or after the time defined in `CUTOFF_HOUR`.
        - As a result, reminders should be scheduled considering that "Day 1" of the
          activation period starts the day after registration.
    Note:
        - This test ensures that the logic for setting dates is working correctly
          for users registered after the cutoff hour.
    """
    FIRST_REMINDER_DAY = timezone.now() + timedelta(
        days=PendingAccountsModel.REMINDER_DAYS["after_cutoff"]["first_day"]
    )

    SECOND_REMINDER_DAY = timezone.now() + timedelta(
        days=PendingAccountsModel.REMINDER_DAYS["after_cutoff"]["second_day"]
    )

    ACTIVATION_DEADLINE_DAY = SECOND_REMINDER_DAY.replace(
        hour=23, minute=59, second=59, microsecond=0
    )

    actual_pending = PendingAccountsModel.objects.create(
        user=user_registered_at_cutoff_hour
    )

    assert actual_pending.first_reminder_at.day == FIRST_REMINDER_DAY.day
    assert actual_pending.second_reminder_at.day == SECOND_REMINDER_DAY.day
    assert actual_pending.activation_deadline == ACTIVATION_DEADLINE_DAY


@pytest.mark.django_db
def test_first_reminder_emails_are_fetched_correctly_for_today(
    create_users_for_reminder,
):
    """
    Test get_first_reminder_accounts_today method correctly returns email addresses
    for users who should be notified today with the first reminder.

    This test:
        - Uses time travel to simulate the system's behavior on the next day.
        - Fetches the email addresses of users who should receive the first reminder.
    """
    # Travel to the next day to check if the system correctly fetched
    # the email addresses that should be notified today.
    with time_machine.travel(FIRST_REMINDER_DAY):
        pending_accounts: list[PendingAccountsModel] = (
            PendingAccountsModel.objects.get_first_reminder_accounts_today()
        )

        actual_emails = []
        for pending_account in pending_accounts:
            actual_emails.append(pending_account.user.email)

        # Assert that only the expected emails for today are fetched.
        for expected_email in EMAILS_INACTIVE_USERS:
            assert expected_email in actual_emails


@pytest.mark.django_db
def test_second_reminder_emails_are_fetched_correctly_for_today(
    create_users_for_reminder,
):
    """
    Test get_second_reminder_accounts_today method correctly returns email addresses
    for users who should be notified today with the second reminder.

    This test:
        - Uses time travel to simulate the system's behavior four days after
          user registration.
        - Fetches the email addresses of users who should receive the second reminder.
    """
    # Travel to the next day to check if the system correctly fetched
    # the email addresses that should be notified today.
    with time_machine.travel(SECOND_REMINDER_DAY):
        pending_accounts: list[PendingAccountsModel] = (
            PendingAccountsModel.objects.get_second_reminder_accounts_today()
        )

        actual_emails = []
        for pending_account in pending_accounts:
            actual_emails.append(pending_account.user.email)

        # Assert that only the expected emails for today are fetched.
        for expected_email in EMAILS_INACTIVE_USERS:
            assert expected_email in actual_emails


@pytest.mark.django_db
def test_accounts_with_expired_deadlines_are_deleted(create_users_for_reminder):
    """
    Tests whether accounts that have not activated their accounts by the timeout
    are actually removed from the system.
    The method that removes these accounts is .delete_expired_accounts().
    """
    with time_machine.travel(DAY_AFTER_ACTIVATION_DEADLINE):
        for user_email in EMAILS_INACTIVE_USERS:
            assert UserProfileModel.objects.filter(email=user_email).exists()

        PendingAccountsModel.objects.delete_expired_accounts()

        for user_email in EMAILS_INACTIVE_USERS:
            assert not UserProfileModel.objects.filter(email=user_email).exists()


@pytest.mark.django_db
def test_deleted_users_have_their_emails_saved_for_notification(
    create_users_for_reminder,
):
    """
    Tests whether accounts that have been removed will have their emails
    persisted for later notification.
    """
    with time_machine.travel(DAY_AFTER_ACTIVATION_DEADLINE):
        PendingAccountsModel.objects.delete_expired_accounts()

        for user_email in EMAILS_INACTIVE_USERS:
            assert UsersPendingDeletionNotificationModel.objects.filter(
                email=user_email
            ).exists()
