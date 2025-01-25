import smtplib

from celery import shared_task
from django.core.management import call_command
from user_app.utils.email_service import send_activation_code_by_email


@shared_task
def task_remove_exp_code():
    """
    Executes the `remove_exp_code` command to remove expired account activation codes,
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
def task_send_activation_code_by_email(self, user_email: str) -> int:
    try:
        sent_count = send_activation_code_by_email(user_email)
        return sent_count
    except smtplib.SMTPException as e:
        raise self.retry(exc=e)
