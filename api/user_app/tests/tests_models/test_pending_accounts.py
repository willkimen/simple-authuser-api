from datetime import timedelta

import pytest
import time_machine
from django.utils import timezone
from user_app.models import UserProfileModel
from user_app.models.user_models import PendingAccounts

# ========== Constants ==================
USER_DATA = {
    "first_name": "Fake Name",
    "last_name": "Fake Last",
    "email": "fake@email.com",
    "is_active": False,
    "password": "FAKEfake123!",
}

# List of email addresses that should *not* receive a reminder today
# because their reminder date is not today.
irrelevant_reminder_emails = [
    "fake1@email.com",
    "fake2@email.com",
    "fake3@email.com",
]

# List of email addresses that should receive a reminder today,
# because their first reminder date is today.
expected_reminder_emails_today = [
    "fake4@email.com",
    "fake5@email.com",
    "fake6@email.com",
]


# ============ Fixtures =========================
@pytest.fixture
def user_registered_before_day_cutoff_hour():
    """
    Fixture that creates and persists a user who was registered one hour before
    the cutoff hour defined by `DAY_CUTOFF_HOUR`.
    """
    before_day_cutoff_hour = timezone.now().replace(
        hour=(PendingAccounts.DAY_CUTOFF_HOUR - 1), minute=00, second=0, microsecond=0
    )

    with time_machine.travel(before_day_cutoff_hour):
        user = UserProfileModel.objects.create_user(**USER_DATA)

    return user


@pytest.fixture
def user_registered_after_day_cutoff_hour():
    """
    Fixture that creates and persists a user who was registered exactly at the
    cutoff hour defined by `DAY_CUTOFF_HOUR`.
    """
    after_day_cutoff_hour = timezone.now().replace(
        hour=PendingAccounts.DAY_CUTOFF_HOUR, minute=00, second=0, microsecond=0
    )

    with time_machine.travel(after_day_cutoff_hour):
        user = UserProfileModel.objects.create_user(**USER_DATA)

    return user


@pytest.fixture
def create_users_for_reminder():
    """
    Fixture that creates multiple users in the database with different
    registration dates.

    This fixture:
        - Creates users who registered **today**, before the cutoff time
          defined by `DAY_CUTOFF_HOUR`.
        - Creates users who registered **two days ago**, simulating a case where they
          should **not** receive a reminder today.

    Usage:
        - This fixture is useful for testing scenarios where users' registration
          dates affect whether they should receive activation reminders.
        - Users created before the cutoff hour will have their reminder dates
          set accordingly.
        - Users created two days earlier will not receive reminders today, based on
          their registration date.

    Details:
        - The first batch of users (created today before `DAY_CUTOFF_HOUR`) will have
          their `PendingAccounts` entries created with the corresponding reminder dates.
        - The second batch of users (created two days ago) will not be considered
          for reminders today.

    Example:
        - The users registered before `DAY_CUTOFF_HOUR` will be eligible for
          today's reminders.
        - The users registered two days ago will not receive reminders today.
    """
    before_day_cutoff_hour = timezone.now().replace(
        hour=(PendingAccounts.DAY_CUTOFF_HOUR - 1), minute=00, second=0, microsecond=0
    )

    with time_machine.travel(before_day_cutoff_hour):
        for email in expected_reminder_emails_today:
            USER_DATA["email"] = email
            user = UserProfileModel.objects.create_user(**USER_DATA)
            PendingAccounts.objects.create(user=user)

    # Time travel to a past date to simulate users who should not get
    # a reminder today (e.g., they were registered two days ago).
    past_reminder_date = timezone.now().replace(
        hour=(PendingAccounts.DAY_CUTOFF_HOUR - 1), minute=00, second=0, microsecond=0
    ) - timedelta(days=2)

    with time_machine.travel(past_reminder_date):
        for email in irrelevant_reminder_emails:
            USER_DATA["email"] = email
            user = UserProfileModel.objects.create_user(**USER_DATA)
            PendingAccounts.objects.create(user=user)


# ============== Tests ==================
@pytest.mark.django_db
def test_reminders_and_deadline_are_set_correctly_when_user_registers_before_cutoff_hour(
    user_registered_before_day_cutoff_hour,
):
    """
    Checks if the reminder dates and activation deadline are correctly set when a
    user registers before the time defined in `DAY_CUTOFF_HOUR`.

    Scenario:
        - A user registers before the cutoff time (`DAY_CUTOFF_HOUR`).
        - As a result, reminders should be scheduled considering that "Day 1" of
          the activation period starts on the registration day itself.

    Validations:
        - `first_reminder_at` should be scheduled according to
          `FIRST_REMINDER_DAYS_BEFORE_DAY_CUTOFF_HOUR` days after registration.
        - `second_reminder_at` should be scheduled according to
          `SECOND_REMINDER_DAYS_BEFORE_DAY_CUTOFF_HOUR` days after registration.
        - `activation_deadline` should be set to the end of the day (23:59) on the
          second reminder date.

    Note:
        - This test ensures that the logic for setting dates is working correctly
          for users registered before the cutoff hour.
    """
    expected_first_reminder_at = timezone.now() + timedelta(
        days=PendingAccounts.FIRST_REMINDER_DAYS_BEFORE_DAY_CUTOFF_HOUR
    )
    expected_second_reminder_at = timezone.now() + timedelta(
        days=PendingAccounts.SECOND_REMINDER_DAYS_BEFORE_DAY_CUTOFF_HOUR
    )
    expected_activation_deadline = expected_second_reminder_at.replace(
        hour=23, minute=59, second=0, microsecond=0
    )

    actual_pending = PendingAccounts.objects.create(
        user=user_registered_before_day_cutoff_hour
    )

    assert actual_pending.first_reminder_at.day == expected_first_reminder_at.day
    assert actual_pending.second_reminder_at.day == expected_second_reminder_at.day
    assert actual_pending.activation_deadline == expected_activation_deadline


@pytest.mark.django_db
def test_reminders_and_deadline_are_set_correctly_when_user_registers_after_cutoff_hour(
    user_registered_after_day_cutoff_hour,
):
    """
    Checks if the reminder dates and activation deadline are correctly set when a
    user registers at or after `DAY_CUTOFF_HOUR`.

    Scenario:
        - A user registers exactly at or after the time defined in `DAY_CUTOFF_HOUR`.
        - As a result, reminders should be scheduled considering that "Day 1" of the
          activation period starts the day after registration.

    Validations:
        - `first_reminder_at` should be scheduled according to
          `FIRST_REMINDER_DAYS_AFTER_DAY_CUTOFF_HOUR` days after registration.
        - `second_reminder_at` should be scheduled according to
          `SECOND_REMINDER_DAYS_AFTER_DAY_CUTOFF_HOUR` days after registration.
        - `activation_deadline` should be set to the end of the day (23:59) on the
          second reminder date.

    Note:
        - This test ensures that the logic for setting dates is working correctly
          for users registered after the cutoff hour.
    """
    expected_first_reminder_at = timezone.now() + timedelta(
        days=PendingAccounts.FIRST_REMINDER_DAYS_AFTER_DAY_CUTOFF_HOUR
    )
    expected_second_reminder_at = timezone.now() + timedelta(
        days=PendingAccounts.SECOND_REMINDER_DAYS_AFTER_DAY_CUTOFF_HOUR
    )
    expected_activation_deadline = expected_second_reminder_at.replace(
        hour=23, minute=59, second=0, microsecond=0
    )

    actual_pending = PendingAccounts.objects.create(
        user=user_registered_after_day_cutoff_hour
    )

    assert actual_pending.first_reminder_at.day == expected_first_reminder_at.day
    assert actual_pending.second_reminder_at.day == expected_second_reminder_at.day
    assert actual_pending.activation_deadline == expected_activation_deadline


@pytest.mark.django_db
def test_first_reminder_emails_are_fetched_correctly_for_today(
    create_users_for_reminder,
):
    """
    Test that verifies the correct fetching of email addresses for users
    who should be notified today with the first reminder.

    This test:
        - Uses time travel to simulate the system's behavior on the next day.
        - Fetches the email addresses of users who should receive the first reminder.
        - Verifies that only the email addresses of users who registered before
          the cutoff time (`DAY_CUTOFF_HOUR`) today are retrieved.
        - Ensures that users who registered earlier (e.g., two days ago) do not
          receive a reminder today.

    Expected behavior:
        - The system should correctly identify the users who need to be notified today.
        - Only emails for users who should receive the first reminder today
          should be included.
    """
    # Travel to the next day to check if the system correctly fetched
    # the email addresses that should be notified today.
    first_reminder_day = timezone.now() + timedelta(
        days=PendingAccounts.FIRST_REMINDER_DAYS_BEFORE_DAY_CUTOFF_HOUR
    )
    with time_machine.travel(first_reminder_day):
        actual_emails_fetched = (
            PendingAccounts.objects.get_first_reminder_emails_today()
        )
        # Assert that only the expected emails for today are fetched.
        for email in expected_reminder_emails_today:
            assert email in actual_emails_fetched

        # Assert that irrelevant emails are not fetched.
        for email in irrelevant_reminder_emails:
            assert not email in actual_emails_fetched


@pytest.mark.django_db
def test_second_reminder_emails_are_fetched_correctly_for_today(
    create_users_for_reminder,
):
    """
    Test that verifies the correct fetching of email addresses for users
    who should be notified today with the second reminder.

    This test:
        - Uses time travel to simulate the system's behavior four days after
          user registration.
        - Fetches the email addresses of users who should receive the second reminder.
        - Verifies that only the email addresses of users who registered before
          the cutoff time (`DAY_CUTOFF_HOUR`) four days ago are retrieved.
        - Ensures that users who registered earlier (e.g., more than four days ago)
          do not receive a second reminder today.

    Expected behavior:
        - The system should correctly identify the users who need to be notified today
          with the second reminder.
        - Only emails for users who should receive the second reminder today should be
          included.
    """
    second_reminder_day = timezone.now() + timedelta(
        days=PendingAccounts.SECOND_REMINDER_DAYS_BEFORE_DAY_CUTOFF_HOUR
    )
    with time_machine.travel(second_reminder_day):
        actual_emails_fetched = (
            PendingAccounts.objects.get_second_reminder_emails_today()
        )
        # Assert that only the expected emails for today are fetched.
        for email in expected_reminder_emails_today:
            assert email in actual_emails_fetched

        # Assert that irrelevant emails are not fetched.
        for email in irrelevant_reminder_emails:
            assert not email in actual_emails_fetched


@pytest.mark.django_db
def test_get_first_reminder_deadline_today(create_users_for_reminder):
    """
    Tests whether the `get_first_reminder_deadline_today` method correctly returns
    the activation deadline for users who should receive their first reminder today.

    This test:
    - Simulates today's date as the first reminder day.
    - Retrieves the expected deadline for users scheduled to receive this reminder.
    - Verifies that the method returns the correct deadline.
    """
    first_reminder_day = timezone.now() + timedelta(
        days=PendingAccounts.FIRST_REMINDER_DAYS_BEFORE_DAY_CUTOFF_HOUR
    )
    with time_machine.travel(first_reminder_day):
        expected_deadline = (
            PendingAccounts.objects.filter(
                first_reminder_at__date=timezone.now().date()
            )
            .values_list("activation_deadline", flat=True)
            .first()
        )

        actual_deadline = PendingAccounts.objects.get_first_reminder_deadline_today()

        assert (
            actual_deadline == expected_deadline
        ), "The first reminder deadline is incorrect."


@pytest.mark.django_db
def test_get_second_reminder_deadline_today(create_users_for_reminder):
    """
    Tests whether the `get_second_reminder_deadline_today` method correctly returns
    the activation deadline for users who should receive their second reminder today.

    This test:
    - Simulates today's date as the second reminder day.
    - Retrieves the expected deadline for users scheduled to receive this reminder.
    - Verifies that the method returns the correct deadline.
    """
    second_reminder_day = timezone.now() + timedelta(
        days=PendingAccounts.SECOND_REMINDER_DAYS_BEFORE_DAY_CUTOFF_HOUR
    )
    with time_machine.travel(second_reminder_day):
        expected_deadline = (
            PendingAccounts.objects.filter(
                second_reminder_at__date=timezone.now().date()
            )
            .values_list("activation_deadline", flat=True)
            .first()
        )

        actual_deadline = PendingAccounts.objects.get_second_reminder_deadline_today()

        assert (
            actual_deadline == expected_deadline
        ), "The second reminder deadline is incorrect."
