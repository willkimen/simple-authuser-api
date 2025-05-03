from datetime import timedelta

import pytest
import time_machine
from celery import states
from celery.result import EagerResult
from django.utils import timezone
from account_auth.models import AccountModel
from account_auth.models.account import PendingAccountsModel
from account_auth.tasks import task_delete_expired_accounts

# ========== Constants ==================
ACCOUNT_DATA = {
    "first_name": "Fake Name",
    "last_name": "Fake Last",
    "email": "fake@email.com",
    "is_active": False,
    "password": "FAKEfake123!",
}

EMAILS_INACTIVE_ACCOUNTS = [
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
def create_accounts_for_reminder():
    """
    Fixture that creates unactivated accounts and associates
    them with PendingAccountsModel.

    This fixture:
        - Creates multiple accounts who registered before the cutoff hour defined
          by `CUTOFF_HOUR`.
        - Associates each account with a PendingAccountsModel instance to represent
          that their accounts are pending activation.
        - Simulates the registration time using time travel to ensure correct
          timestamps for reminder logic.
    """
    with time_machine.travel(TODAY_BEFORE_CUTOFF):
        for email in EMAILS_INACTIVE_ACCOUNTS:
            ACCOUNT_DATA["email"] = email
            account = AccountModel.objects.create_user(**ACCOUNT_DATA)
            PendingAccountsModel.objects.create(account=account)


# ========== Tests ==================
@pytest.mark.django_db
def test_deleted_expired_accounts(create_accounts_for_reminder):
    """
    Test deletion of unactivated accounts that have passed
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
        for email in EMAILS_INACTIVE_ACCOUNTS:
            assert AccountModel.objects.filter(email=email).exists()

        result: EagerResult = task_delete_expired_accounts.apply()

        assert result.status == states.SUCCESS
        for email in EMAILS_INACTIVE_ACCOUNTS:
            assert not AccountModel.objects.filter(email=email).exists()


@pytest.mark.django_db
def test_expired_account_not_deleted_before_scheduled_time(create_accounts_for_reminder):
    """
    Verifies that inactive accounts are not deleted when the deadline
    has not yet passed.
    """
    with time_machine.travel(ACTIVATION_DEADLINE_DAY):
        for email in EMAILS_INACTIVE_ACCOUNTS:
            assert AccountModel.objects.filter(email=email).exists()

        result: EagerResult = task_delete_expired_accounts.apply()

        assert result.status == states.SUCCESS
        for email in EMAILS_INACTIVE_ACCOUNTS:
            assert AccountModel.objects.filter(email=email).exists()
