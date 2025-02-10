import smtplib

from celery import shared_task
from django.core.management import call_command
from user_app.utils.email_service import (
    notify_activated_account,
    notify_changed_email,
    notify_reset_password,
    send_account_activation_code,
    send_email_change_code,
    send_reset_password_code,
)


@shared_task
def task_remove_exp_code():
    """
    Executes the `remove_exp_code` command to remove expired account verification codes,
    email change codes, and password reset codes.
    """
    call_command("remove_exp_code")


@shared_task
def task_remove_exp_token():
    """
    Executes the `remove_exp_token` command to remove expired validation tokens and
    tokens in the blacklist.
    """
    call_command("remove_exp_token")


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
