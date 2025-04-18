from datetime import timedelta

import pytest
import time_machine
from celery import states
from celery.result import EagerResult
from django.utils import timezone
from user_app.models import UserProfileModel
from user_app.models.user_models import PendingAccountsModel
from user_app.tasks import task_delete_expired_accounts

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

# Set the date for the second reminder
SECOND_REMINDER_DAY = timezone.now() + timedelta(
    days=PendingAccountsModel.REMINDER_DAYS["before_cutoff"]["second_day"]
)

# Sets the deadline date for account activation.
ACTIVATION_DEADLINE_DAY = SECOND_REMINDER_DAY.replace(
    hour=23, minute=59, second=59, microsecond=0
)


# ============ Fixtures =========================
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


# ========== Tests ==================
@pytest.mark.django_db
def test_deleted_expired_accounts(create_users_for_reminder):
    """
    Test deletion of unactivated user accounts that have passed
    their activation deadline.

    This test verifies the behavior of the `task_delete_expired_accounts` task,
    which is scheduled to run every day at 00:00 (midnight) using celery beat.

    Considerations:
    - The task runs one day after the activation deadline.
    - This ensures precise removal of accounts that have not been activated
      within the specified time frame.
    """
    day_after_activation_deadline = ACTIVATION_DEADLINE_DAY + timedelta(seconds=1)

    with time_machine.travel(day_after_activation_deadline):
        for user_email in EMAILS_INACTIVE_USERS:
            assert UserProfileModel.objects.filter(email=user_email).exists()

        result: EagerResult = task_delete_expired_accounts.apply()

        assert result.status == states.SUCCESS
        for user_email in EMAILS_INACTIVE_USERS:
            assert not UserProfileModel.objects.filter(email=user_email).exists()


@pytest.mark.django_db
def test_expired_account_not_deleted_before_scheduled_time(create_users_for_reminder):
    """
    Verifies that inactive user accounts are not deleted when the deadline
    has not yet passed.
    """
    with time_machine.travel(ACTIVATION_DEADLINE_DAY):
        for user_email in EMAILS_INACTIVE_USERS:
            assert UserProfileModel.objects.filter(email=user_email).exists()

        result: EagerResult = task_delete_expired_accounts.apply()

        assert result.status == states.SUCCESS
        for user_email in EMAILS_INACTIVE_USERS:
            assert UserProfileModel.objects.filter(email=user_email).exists()
