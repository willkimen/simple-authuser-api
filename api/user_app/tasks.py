import smtplib

from celery import shared_task
from django.utils import timezone
from user_app.email.email_service import (
    notify_activated_account,
    notify_changed_email,
    notify_deleted_account,
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
    ResetPasswordCodeModel,
    ValidTokenModel,
)


@shared_task
def task_remove_exp_code():
    """
    Remove all codes with an expiration date earlier than the current date.
    """
    now = timezone.now()
    AccountActivationCodeModel.objects.filter(expires_at__lt=now).delete()
    ChangeEmailCodeModel.objects.filter(expires_at__lt=now).delete()
    ResetPasswordCodeModel.objects.filter(expires_at__lt=now).delete()


@shared_task
def task_remove_exp_token():
    """
    Remove expired validation tokens and expired tokens in the blacklist.
    """
    now = timezone.now()
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
        sent_count = send_account_activation_code(user_email)
        return sent_count
    except smtplib.SMTPException as e:
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
        sent_count = send_email_change_code(actual_email, new_email)
        return sent_count
    except smtplib.SMTPException as e:
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
        sent_count = send_reset_password_code(user_email)
        return sent_count
    except smtplib.SMTPException as e:
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
        sent_count = notify_activated_account(user_email)
        return sent_count
    except smtplib.SMTPException as e:
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
        sent_count = notify_changed_email(user_email)
        return sent_count
    except smtplib.SMTPException as e:
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
        sent_count = notify_reset_password(user_email)
        return sent_count
    except smtplib.SMTPException as e:
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
        sent_count = notify_deleted_account(user_email)
        return sent_count
    except smtplib.SMTPException as e:
        raise self.retry(exc=e)


@shared_task(bind=True, retry_backoff=True, max_retries=5)
def task_notify_first_reminder(self) -> int:
    """
    Celery task to send the first reminder notification email to users
    informing them that they have not activated their accounts.
    If an SMTP exception occurs, the task will automatically
    retry up to five times with exponential backoff.
    """
    try:
        sent_count = notify_first_reminder()
        return sent_count
    except smtplib.SMTPException as e:
        raise self.retry(exc=e)


@shared_task(bind=True, retry_backoff=True, max_retries=5)
def task_notify_second_reminder(self) -> int:
    """
    Celery task to send the second reminder notification email to users
    informing them that they have not activated their accounts.
    If an SMTP exception occurs, the task will automatically
    retry up to five times with exponential backoff.
    """
    try:
        sent_count = notify_second_reminder()
        return sent_count
    except smtplib.SMTPException as e:
        raise self.retry(exc=e)
