import logging
import smtplib
from datetime import datetime

from celery import Task, chain, shared_task
from dateutil.parser import parse
from django.utils import timezone
from user_app.constants.celery import MAX_RETRIES, RETRY_BACKOFF_MAX
from user_app.constants.logging import (
    EMAIL_TASK_ERROR_LOGGER_NAME,
    FAILED_NOTIFY_ACTIVATED_ACCOUNT_TAG,
    FAILED_NOTIFY_CHANGED_EMAIL_TAG,
    FAILED_NOTIFY_DELETED_ACCOUNT_TAG,
    FAILED_NOTIFY_EXPIRED_ACCOUNT_DELETION_TAG,
    FAILED_NOTIFY_FIRST_REMINDER_TAG,
    FAILED_NOTIFY_RESET_PASSWORD_TAG,
    FAILED_NOTIFY_SECOND_REMINDER_TAG,
    FAILED_SEND_ACCOUNT_ACTIVATION_CODE_TAG,
    FAILED_SEND_EMAIL_CHANGE_CODE_TAG,
    FAILED_SEND_RESET_PASSWORD_CODE_TAG,
    email_task_error_message_format,
)
from user_app.email.email_service import (
    notify_activated_account,
    notify_activation_account_reminder,
    notify_changed_email,
    notify_deleted_account,
    notify_expired_account_deletion,
    notify_reset_password,
    send_account_activation_code,
    send_email_change_code,
    send_reset_password_code,
)
from user_app.models import (
    AccountActivationCodeModel,
    BlacklistTokenModel,
    ChangeEmailCodeModel,
    FailedTaskModel,
    PendingAccountsModel,
    ResetPasswordCodeModel,
    ValidTokenModel,
)

logger = logging.getLogger(EMAIL_TASK_ERROR_LOGGER_NAME)


def get_emails_and_deadline(is_first_reminder: bool) -> tuple[list[str], datetime]:
    """
    Fetches the emails of accounts who need to be notified about their pending
    account activation.
    Also returns the activation deadline for the accounts.

    Args:
        is_first_reminder (bool): Indicates whether this is the first
                                  or second reminder.

    Returns:
        tuple[list[str], datetime]: A tuple containing a list of emails and
                                    the account activation deadline.
    """
    pending_accounts: list[PendingAccountsModel] = []
    if is_first_reminder:
        pending_accounts = (
            PendingAccountsModel.objects.get_first_reminder_accounts_today()
        )
    else:
        pending_accounts = (
            PendingAccountsModel.objects.get_second_reminder_accounts_today()
        )

    if not pending_accounts:
        return ([], None)

    # Extract emails and activation_deadline
    emails = [pa.account.email for pa in pending_accounts]
    activation_deadline: datetime = pending_accounts[0].activation_deadline

    return (emails, activation_deadline)


class TaskFailure(Task):
    """
    This class provides a way to log task failure details by creating a database
    record whenever a task fails.
    It captures the task name, ID, arguments, exception message, and traceback.
    """

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        FailedTaskModel.objects.create(
            task_name=self.name,
            task_id=task_id,
            args=args,
            kwargs=kwargs,
            exception=str(exc),
            traceback=str(einfo.traceback),
        )

        super().on_failure(exc, task_id, args, kwargs, einfo)


@shared_task
def task_remove_exp_code() -> None:
    """
    Remove all codes with an expiration date earlier than the current date.
    This task must be called via a schedule.
    """
    now: datetime = timezone.now()
    AccountActivationCodeModel.objects.filter(expires_at__lt=now).delete()
    ChangeEmailCodeModel.objects.filter(expires_at__lt=now).delete()
    ResetPasswordCodeModel.objects.filter(expires_at__lt=now).delete()


@shared_task
def task_remove_exp_token() -> None:
    """
    Remove expired tokens.
    This task must be called via a schedule.
    """
    now: datetime = timezone.now()
    ValidTokenModel.objects.filter(exp__lt=now).delete()
    BlacklistTokenModel.objects.filter(exp__lt=now).delete()


@shared_task(
    bind=True,
    base=TaskFailure,
    retry_backoff=True,
    retry_backoff_max=RETRY_BACKOFF_MAX,
    max_retries=MAX_RETRIES,
)
def task_send_account_activation_code(self, email: str) -> int:
    """
    Celery task to send an activation code via email.

    This task attempts to send a verification code to the account's email address.
    If an SMTP exception occurs, the task will automatically retry up with
    exponential backoff.
    """
    try:
        sent_count: int = send_account_activation_code(email)
        return sent_count
    except smtplib.SMTPException as e:
        # Logs the error after the last retry attempt.
        if self.request.retries == self.max_retries:
            logger.email_task_error(
                email_task_error_message_format.format(
                    tag=FAILED_SEND_ACCOUNT_ACTIVATION_CODE_TAG,
                    task_id=self.request.id,
                    to=email,
                    error=str(e),
                )
            )
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    base=TaskFailure,
    retry_backoff=True,
    retry_backoff_max=RETRY_BACKOFF_MAX,
    max_retries=MAX_RETRIES,
)
def task_send_email_change_code(self, actual_email: str, new_email: str) -> int:
    """
    Celery task to send a verification code for changing the account's email.

    This task attempts to send a verification code tothe new email (`new_email`).
    If an SMTP exception occurs, the task will automatically retry up with
    exponential backoff.
    """
    try:
        sent_count: int = send_email_change_code(actual_email, new_email)
        return sent_count
    except smtplib.SMTPException as e:
        # Logs the error after the last retry attempt.
        if self.request.retries == self.max_retries:
            to = f"{actual_email},{new_email}"
            logger.email_task_error(
                email_task_error_message_format.format(
                    tag=FAILED_SEND_EMAIL_CHANGE_CODE_TAG,
                    task_id=self.request.id,
                    to=to,
                    error=str(e),
                )
            )
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    base=TaskFailure,
    retry_backoff=True,
    retry_backoff_max=RETRY_BACKOFF_MAX,
    max_retries=MAX_RETRIES,
)
def task_send_reset_password_code(self, email: str) -> int:
    """
    Celery task to send a password reset verification code via email.

    This task attempts to send a verification code to the account's email address
    to allow password reset. If an SMTP exception occurs, the task will automatically
    retry up with exponential backoff.
    """
    try:
        sent_count: int = send_reset_password_code(email)
        return sent_count
    except smtplib.SMTPException as e:
        # Logs the error after the last retry attempt.
        if self.request.retries == self.max_retries:
            logger.email_task_error(
                email_task_error_message_format.format(
                    tag=FAILED_SEND_RESET_PASSWORD_CODE_TAG,
                    task_id=self.request.id,
                    to=email,
                    error=str(e),
                )
            )
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    base=TaskFailure,
    retry_backoff=True,
    retry_backoff_max=RETRY_BACKOFF_MAX,
    max_retries=MAX_RETRIES,
)
def task_notify_activated_account(self, email: str) -> int:
    """
    Celery task to send a notification email informing the account that their
    account has been activated.
    If an SMTP exception occurs, the task will automatically
    retry up with exponential backoff.
    """
    try:
        sent_count: int = notify_activated_account(email)
        return sent_count
    except smtplib.SMTPException as e:
        # Logs the error after the last retry attempt.
        if self.request.retries == self.max_retries:
            logger.email_task_error(
                email_task_error_message_format.format(
                    tag=FAILED_NOTIFY_ACTIVATED_ACCOUNT_TAG,
                    task_id=self.request.id,
                    to=email,
                    error=str(e),
                )
            )
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    base=TaskFailure,
    retry_backoff=True,
    retry_backoff_max=RETRY_BACKOFF_MAX,
    max_retries=MAX_RETRIES,
)
def task_notify_changed_email(self, email: str) -> int:
    """
    Celery task to send a notification email informing the account that their
    email addredd has been changed.
    If an SMTP exception occurs, the task will automatically
    retry up with exponential backoff.
    """
    try:
        sent_count: int = notify_changed_email(email)
        return sent_count
    except smtplib.SMTPException as e:
        # Logs the error after the last retry attempt.
        if self.request.retries == self.max_retries:
            logger.email_task_error(
                email_task_error_message_format.format(
                    tag=FAILED_NOTIFY_CHANGED_EMAIL_TAG,
                    task_id=self.request.id,
                    to=email,
                    error=str(e),
                )
            )
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    base=TaskFailure,
    retry_backoff=True,
    retry_backoff_max=RETRY_BACKOFF_MAX,
    max_retries=MAX_RETRIES,
)
def task_notify_reset_password(self, email: str) -> int:
    """
    Celery task to send a notification email informing the account that their
    password has been reset.
    If an SMTP exception occurs, the task will automatically
    retry up with exponential backoff.
    """
    try:
        sent_count: int = notify_reset_password(email)
        return sent_count
    except smtplib.SMTPException as e:
        # Logs the error after the last retry attempt.
        if self.request.retries == self.max_retries:
            logger.email_task_error(
                email_task_error_message_format.format(
                    tag=FAILED_NOTIFY_RESET_PASSWORD_TAG,
                    task_id=self.request.id,
                    to=email,
                    error=str(e),
                )
            )
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    base=TaskFailure,
    retry_backoff=True,
    retry_backoff_max=RETRY_BACKOFF_MAX,
    max_retries=MAX_RETRIES,
)
def task_notify_deleted_account(self, email: str) -> int:
    """
    Celery task to send a notification email informing the account that their
    account has been deleted.
    If an SMTP exception occurs, the task will automatically
    retry up with exponential backoff.
    """
    try:
        sent_count: int = notify_deleted_account(email)
        return sent_count
    except smtplib.SMTPException as e:
        # Logs the error after the last retry attempt.
        if self.request.retries == self.max_retries:
            logger.email_task_error(
                email_task_error_message_format.format(
                    tag=FAILED_NOTIFY_DELETED_ACCOUNT_TAG,
                    task_id=self.request.id,
                    to=email,
                    error=str(e),
                )
            )
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    base=TaskFailure,
    retry_backoff=True,
    retry_backoff_max=RETRY_BACKOFF_MAX,
    max_retries=MAX_RETRIES,
)
def task_notify_first_reminder(
    self, emails: list[str], activation_deadline: datetime | str
) -> int:
    """
    Celery task to send the first reminder notification email to accounts
    informing them that they have not activated their accounts.
    If an SMTP exception occurs, the task will automatically
    retry up with exponential backoff.
    """
    # If the date comes in ISO string format, convert it to datetime type.
    if isinstance(activation_deadline, str):
        activation_deadline = parse(activation_deadline)

    try:
        sent_count: int = notify_activation_account_reminder(
            emails, activation_deadline
        )
        return sent_count
    except smtplib.SMTPException as e:
        # Logs the error after the last retry attempt.
        if self.request.retries == self.max_retries:
            logger.email_task_error(
                email_task_error_message_format.format(
                    tag=FAILED_NOTIFY_FIRST_REMINDER_TAG,
                    task_id=self.request.id,
                    to=",".join(emails),
                    error=str(e),
                )
            )
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    base=TaskFailure,
    retry_backoff=True,
    retry_backoff_max=RETRY_BACKOFF_MAX,
    max_retries=MAX_RETRIES,
)
def task_notify_second_reminder(
    self, emails: list[str], activation_deadline: datetime | str
) -> int:
    """
    Celery task to send the second reminder notification email to accounts
    informing them that they have not activated their accounts.
    If an SMTP exception occurs, the task will automatically
    retry up with exponential backoff.
    """

    # If the date comes in ISO string format, convert it to datetime type.
    if isinstance(activation_deadline, str):
        activation_deadline = parse(activation_deadline)

    try:
        sent_count: int = notify_activation_account_reminder(
            emails, activation_deadline
        )
        return sent_count
    except smtplib.SMTPException as e:
        # Logs the error after the last retry attempt.
        if self.request.retries == self.max_retries:
            logger.email_task_error(
                email_task_error_message_format.format(
                    tag=FAILED_NOTIFY_SECOND_REMINDER_TAG,
                    task_id=self.request.id,
                    to=",".join(emails),
                    error=str(e),
                )
            )
        raise self.retry(exc=e)


@shared_task
def wrapper_task_notify_first_reminder() -> None:
    """
    Wrapper task to handle the first reminder notification.

    It separates the logic of retrieving account emails and activation deadline
    from the actual task that sends the reminder notification.
    """
    emails, activation_deadline = get_emails_and_deadline(is_first_reminder=True)
    if emails and activation_deadline:
        task_notify_first_reminder.delay(emails, activation_deadline)


@shared_task
def wrapper_task_notify_second_reminder() -> None:
    """
    Wrapper task to handle the second reminder notification.

    It separates the logic of retrieving account emails and activation deadline
    from the actual task that sends the reminder notification.
    """
    emails, activation_deadline = get_emails_and_deadline(is_first_reminder=False)
    if emails and activation_deadline:
        task_notify_second_reminder.delay(emails, activation_deadline)


@shared_task
def task_delete_expired_accounts():
    """
    Task that deletes accounts who have not activated their accounts in a timely manner.
    """
    PendingAccountsModel.objects.delete_expired_accounts()


@shared_task(
    bind=True,
    base=TaskFailure,
    retry_backoff=True,
    retry_backoff_max=RETRY_BACKOFF_MAX,
    max_retries=MAX_RETRIES,
)
def task_notify_expired_account_deletion(self) -> int:
    """
    Task to send the notification email to accounts informing about the removal
    of their accounts from the system, for not activating them in a timely manner.
    After successful sending, these emails are removed.

    If an SMTP exception occurs, the task will automatically
    retry up with exponential backoff.

    Note:
        This task must be scheduled to run **after** `task_delete_expired_accounts`,
        since it relies on the emails collected during the account deletion process.
    """
    try:
        sent_count, _ = notify_expired_account_deletion()
        return sent_count
    except smtplib.SMTPException as e:
        if self.request.retries == self.max_retries:
            logger.email_task_error(
                email_task_error_message_format.format(
                    tag=FAILED_NOTIFY_EXPIRED_ACCOUNT_DELETION_TAG,
                    task_id=self.request.id,
                    to="",
                    error=str(e),
                )
            )
        raise self.retry(exc=e)


@shared_task
def task_delete_expired_accounts_and_notify():
    """
    Celery task that orchestrates the full cleanup flow of expired accounts.

    This task performs the following steps:
        1. Deletes accounts who failed to activate their accounts within the allowed time,
           and stores their emails in a notification table.
        2. After successful deletion, sends an email notification to those accounts,
           informing them about the account removal.

    Implementation note:
        - This task uses a Celery `chain` to ensure that the notification task is only
          executed if the deletion task completes successfully.
        - It replaces the need for scheduling the two tasks independently via Celery Beat.
        - Only this task should be scheduled periodically (e.g., daily at 00:00).
    """
    chain(
        task_delete_expired_accounts.s(), task_notify_expired_account_deletion.s()
    ).apply_async()
