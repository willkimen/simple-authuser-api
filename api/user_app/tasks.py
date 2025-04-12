import logging
import smtplib
from datetime import date, datetime, timedelta

from celery import shared_task
from django.utils import timezone
from user_app.constants.logs_constants import (
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
    notify_changed_email,
    notify_deleted_account,
    notify_expired_account_deletion,
    notify_first_reminder,
    notify_reset_password,
    notify_second_reminder,
    send_account_activation_code,
    send_email_change_code,
    send_reset_password_code,
)
from user_app.models import (
    AccountActivationCodeModel,
    BlacklistTokenModel,
    ChangeEmailCodeModel,
    PendingAccountsModel,
    ResetPasswordCodeModel,
    UsersPendingDeletionNotificationModel,
    ValidTokenModel,
)

logger = logging.getLogger(EMAIL_TASK_ERROR_LOGGER_NAME)


@shared_task
def task_remove_exp_code() -> None:
    """
    Remove all codes with an expiration date earlier than the current date.
    """
    now: datetime = timezone.now()
    AccountActivationCodeModel.objects.filter(expires_at__lt=now).delete()
    ChangeEmailCodeModel.objects.filter(expires_at__lt=now).delete()
    ResetPasswordCodeModel.objects.filter(expires_at__lt=now).delete()


@shared_task
def task_remove_exp_token() -> None:
    """
    Remove expired validation tokens and expired tokens in the blacklist.
    """
    now: datetime = timezone.now()
    ValidTokenModel.objects.filter(exp__lt=now).delete()
    BlacklistTokenModel.objects.filter(exp__lt=now).delete()


@shared_task(bind=True, retry_backoff=True, max_retries=5)
def task_send_account_activation_code(self, user_email: str) -> int:
    """
    Celery task to send an activation code via email.

    This task attempts to send a verification code to the user's email address.
    If an SMTP exception occurs, the task will automatically retry up to five times
    with exponential backoff.
    """
    try:
        sent_count: int = send_account_activation_code(user_email)
        return sent_count
    except smtplib.SMTPException as e:
        if self.request.retries == self.max_retries:
            logger.email_task_error(
                email_task_error_message_format.format(
                    tag=FAILED_SEND_ACCOUNT_ACTIVATION_CODE_TAG,
                    to=user_email,
                    error=str(e),
                )
            )
        raise self.retry(exc=e)


@shared_task(bind=True, retry_backoff=True, max_retries=5)
def task_send_email_change_code(self, actual_email: str, new_email: str) -> int:
    """
    Celery task to send a verification code for changing the user's email.

    This task attempts to send a verification code tothe new email (`new_email`).
    If an SMTP exception occurs, the task will automatically retry up to five times
    with exponential backoff.
    """
    try:
        sent_count: int = send_email_change_code(actual_email, new_email)
        return sent_count
    except smtplib.SMTPException as e:
        if self.request.retries == self.max_retries:
            to = f"{actual_email},{new_email}"
            logger.email_task_error(
                email_task_error_message_format.format(
                    tag=FAILED_SEND_EMAIL_CHANGE_CODE_TAG, to=to, error=str(e)
                )
            )
        raise self.retry(exc=e)


@shared_task(bind=True, retry_backoff=True, max_retries=5)
def task_send_reset_password_code(self, user_email: str) -> int:
    """
    Celery task to send a password reset verification code via email.

    This task attempts to send a verification code to the user's email address
    to allow password reset. If an SMTP exception occurs, the task will automatically
    retry up to five times with exponential backoff.
    """
    try:
        sent_count: int = send_reset_password_code(user_email)
        return sent_count
    except smtplib.SMTPException as e:
        if self.request.retries == self.max_retries:
            logger.email_task_error(
                email_task_error_message_format.format(
                    tag=FAILED_SEND_RESET_PASSWORD_CODE_TAG, to=user_email, error=str(e)
                )
            )
        raise self.retry(exc=e)


@shared_task(bind=True, retry_backoff=True, max_retries=5)
def task_notify_activated_account(self, user_email: str) -> int:
    """
    Celery task to send a notification email informing the user that their
    account has been activated.
    If an SMTP exception occurs, the task will automatically
    retry up to five times with exponential backoff.
    """
    try:
        sent_count: int = notify_activated_account(user_email)
        return sent_count
    except smtplib.SMTPException as e:
        if self.request.retries == self.max_retries:
            logger.email_task_error(
                email_task_error_message_format.format(
                    tag=FAILED_NOTIFY_ACTIVATED_ACCOUNT_TAG, to=user_email, error=str(e)
                )
            )
        raise self.retry(exc=e)


@shared_task(bind=True, retry_backoff=True, max_retries=5)
def task_notify_changed_email(self, user_email: str) -> int:
    """
    Celery task to send a notification email informing the user that their
    email addredd has been changed.
    If an SMTP exception occurs, the task will automatically
    retry up to five times with exponential backoff.
    """
    try:
        sent_count: int = notify_changed_email(user_email)
        return sent_count
    except smtplib.SMTPException as e:
        if self.request.retries == self.max_retries:
            logger.email_task_error(
                email_task_error_message_format.format(
                    tag=FAILED_NOTIFY_CHANGED_EMAIL_TAG, to=user_email, error=str(e)
                )
            )
        raise self.retry(exc=e)


@shared_task(bind=True, retry_backoff=True, max_retries=5)
def task_notify_reset_password(self, user_email: str) -> int:
    """
    Celery task to send a notification email informing the user that their
    password has been reset.
    If an SMTP exception occurs, the task will automatically
    retry up to five times with exponential backoff.
    """
    try:
        sent_count: int = notify_reset_password(user_email)
        return sent_count
    except smtplib.SMTPException as e:
        if self.request.retries == self.max_retries:
            logger.email_task_error(
                email_task_error_message_format.format(
                    tag=FAILED_NOTIFY_RESET_PASSWORD_TAG, to=user_email, error=str(e)
                )
            )
        raise self.retry(exc=e)


@shared_task(bind=True, retry_backoff=True, max_retries=5)
def task_notify_deleted_account(self, user_email: str) -> int:
    """
    Celery task to send a notification email informing the user that their
    account has been deleted.
    If an SMTP exception occurs, the task will automatically
    retry up to five times with exponential backoff.
    """
    try:
        sent_count: int = notify_deleted_account(user_email)
        return sent_count
    except smtplib.SMTPException as e:
        if self.request.retries == self.max_retries:
            logger.email_task_error(
                email_task_error_message_format.format(
                    tag=FAILED_NOTIFY_DELETED_ACCOUNT_TAG, to=user_email, error=str(e)
                )
            )
        raise self.retry(exc=e)


@shared_task(bind=True, retry_backoff=True, max_retries=5)
def task_notify_first_reminder(self) -> int:
    """
    Celery task to send the first reminder notification email to users
    informing them that they have not activated their accounts.
    If an SMTP exception occurs, the task will automatically
    retry up to five times with exponential backoff.
    """
    emails_for_reminder_today: list[str] = (
        PendingAccountsModel.objects.get_first_reminder_emails_today()
    )

    try:
        sent_count: int = notify_first_reminder()
        return sent_count
    except smtplib.SMTPException as e:
        if self.request.retries == self.max_retries:
            logger.email_task_error(
                email_task_error_message_format.format(
                    tag=FAILED_NOTIFY_FIRST_REMINDER_TAG,
                    to=",".join(emails_for_reminder_today),
                    error=str(e),
                )
            )
        raise self.retry(exc=e)


@shared_task(bind=True, retry_backoff=True, max_retries=5)
def task_notify_second_reminder(self) -> int:
    """
    Celery task to send the second reminder notification email to users
    informing them that they have not activated their accounts.
    If an SMTP exception occurs, the task will automatically
    retry up to five times with exponential backoff.
    """
    emails_for_reminder_today: list[str] = (
        PendingAccountsModel.objects.get_second_reminder_emails_today()
    )

    try:
        sent_count: int = notify_second_reminder()
        return sent_count
    except smtplib.SMTPException as e:
        if self.request.retries == self.max_retries:
            logger.email_task_error(
                email_task_error_message_format.format(
                    tag=FAILED_NOTIFY_SECOND_REMINDER_TAG,
                    to=",".join(emails_for_reminder_today),
                    error=str(e),
                )
            )
        raise self.retry(exc=e)


@shared_task
def task_delete_expired_accounts():
    """
    Task that deletes users who have not activated their accounts in a timely manner.

    - Note:
        This task will be scheduled to run every day at 00:00, i.e. one day after
        activation_deadline, so to delete users on the correct day you will need
        to enter yesterday's date.
    """
    yesterday: date = timezone.now().date() - timedelta(days=1)
    PendingAccountsModel.objects.delete_expired_accounts(yesterday)


@shared_task(bind=True, retry_backoff=True, max_retries=5)
def task_notify_expired_account_deletion(self) -> int:
    """
    Celery task to send the notification email to users informing about the removal
    of their accounts from the system, for not activating them in a timely manner.
    After successful sending, these emails are removed.

    If an SMTP exception occurs, the task will automatically
    retry up to five times with exponential backoff.
    """
    emails: list[str] = list(
        UsersPendingDeletionNotificationModel.objects.values_list("email", flat=True)
    )

    try:
        sent_count: int = notify_expired_account_deletion()
        return sent_count
    except smtplib.SMTPException as e:
        if self.request.retries == self.max_retries:
            logger.email_task_error(
                email_task_error_message_format.format(
                    tag=FAILED_NOTIFY_EXPIRED_ACCOUNT_DELETION_TAG,
                    to=",".join(emails),
                    error=str(e),
                )
            )
        raise self.retry(exc=e)
