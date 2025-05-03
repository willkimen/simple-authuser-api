"""
This module contains functions for sending emails related to account actions, 
such as account changes and notifications. It handles the creation and 
sending of verification codes and notification messages to the account.
"""

import smtplib
from datetime import datetime

from account_auth.constants.verification_code import (
    ACTIVATE_ACCOUNT_PREFIX,
    CHANGE_EMAIL_PREFIX,
    RESET_PASSWORD_PREFIX,
)
from account_auth.email.email_classes import (
    ActivationCodeEmail,
    ActivationNotificationEmail,
    ChangeCodeEmail,
    ChangeNotificationEmail,
    DeactivatedAccountNotificationEmail,
    DeletedAccountNotificationEmail,
    ExpiredAccountDeletionEmail,
    PasswordResetNotificationEmail,
    ResetPasswordCodeEmail,
)
from account_auth.models import (
    AccountActivationCodeModel,
    AccountsPendingDeletionNotificationModel,
    ChangeEmailCodeModel,
    ResetPasswordCodeModel,
)


def send_email_change_code(actual_email: str, new_email: str) -> int:
    """
    Sends an email with a verification code to change the account's email address.

    This function generates a random verification code for changing the account's email,
    sends the code to the new email address, and stores the code.
    """

    # Creates code and verify if already exists in database
    code: str = ChangeEmailCodeModel.objects.verify_and_return_new_code(
        prefix=CHANGE_EMAIL_PREFIX
    )

    # Instance of a class that encapsulates the email sending logic.
    email_change = ChangeCodeEmail(
        actual_email=actual_email, new_email=new_email, code=code
    )

    # Sends the email and gets the count of successfully sent emails.
    try:
        sent_count: int = email_change.send_with_error_handling()
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    # Persists code in database.
    ChangeEmailCodeModel.objects.create(
        code=email_change.code,
        account_id=email_change.actual_email,
        new_email=email_change.new_email,
    )
    # Removes all verification codes for an account, except the most recent one.
    ChangeEmailCodeModel.objects.keep_latest_code(email_change.actual_email)

    return sent_count


def send_account_activation_code(email: str) -> int:
    """
    Sends an account activation email to the account with a verification code.

    This function generates a random code for account activation, sends it to the
    account's email, and saves the code and email in the database. The activation code is
    used for verifying the account's email during the registration process.
    """

    # Creates code and verify if already exists in database
    code: str = AccountActivationCodeModel.objects.verify_and_return_new_code(
        prefix=ACTIVATE_ACCOUNT_PREFIX
    )

    # Instance of a class that encapsulates the email sending logic.
    email_activation = ActivationCodeEmail(email=email, code=code)

    # Sends the email and gets the count of successfully sent emails.
    try:
        sent_count: int = email_activation.send_with_error_handling()
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    # Persists code in database.
    AccountActivationCodeModel.objects.create(
        code=email_activation.code, account_id=email_activation.email
    )
    # Removes all verification codes for an account, except the most recent one.
    AccountActivationCodeModel.objects.keep_latest_code(email_activation.email)

    return sent_count


def send_reset_password_code(email: str) -> int:
    """
    Sends a password reset code to the account's email address.

    This function generates a unique password reset code and sends it via email
    to the provided email address.
    The email contains the reset code and instructions. If an error occurs
    during the email sending process, the exception is raised and handled accordingly.
    """

    # Creates code and verify if already exists in database
    code: str = ResetPasswordCodeModel.objects.verify_and_return_new_code(
        prefix=RESET_PASSWORD_PREFIX
    )

    # Instance of a class that encapsulates the email sending logic.
    email_reset = ResetPasswordCodeEmail(email=email, code=code)

    # Sends the email and gets the count of successfully sent emails.
    try:
        sent_count: int = email_reset.send_with_error_handling()
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    # Persists code in database.
    ResetPasswordCodeModel.objects.create(
        code=email_reset.code, account_id=email_reset.email
    )
    # Removes all verification codes for an account, except the most recent one.
    ResetPasswordCodeModel.objects.keep_latest_code(email_reset.email)

    return sent_count


def notify_activated_account(email: str) -> int:
    """
    Sends a notification email to the account informing them that their account
    has been activated.
    """

    # Instance of a class that encapsulates the email sending logic.
    email_notification = ActivationNotificationEmail(email=email)

    # Sends the email and gets the count of successfully sent emails.
    try:
        sent_count: int = email_notification.send_with_error_handling()
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    return sent_count


def notify_changed_email(email: str) -> int:
    """
    Sends a notification email to the account informing them that their email address
    has been changed.
    """
    # Instance of a class that encapsulates the email sending logic.
    email_notification = ChangeNotificationEmail(new_email=email)

    # Sends the email and gets the count of successfully sent emails.
    try:
        sent_count: int = email_notification.send_with_error_handling()
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    return sent_count


def notify_reset_password(email: str) -> int:
    """
    Sends a notification email to the account informing them that their passoword
    has been reset.
    """
    # Instance of a class that encapsulates the email sending logic.
    email_notification = PasswordResetNotificationEmail(email=email)

    # Sends the email and gets the count of successfully sent emails.
    try:
        sent_count: int = email_notification.send_with_error_handling()
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    return sent_count


def notify_deleted_account(email: str) -> int:
    """
    Sends a notification email to the account informing them that their account
    has been deleted.
    """
    # Instance of a class that encapsulates the email sending logic.
    email_notification = DeletedAccountNotificationEmail(email=email)

    # Sends the email and gets the count of successfully sent emails.
    try:
        sent_count: int = email_notification.send_with_error_handling()
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    return sent_count


def notify_activation_account_reminder(
    emails: list[str], activation_deadline: datetime
) -> int:
    """
    Sends the reminder email to accounts who have not yet activated their
    accounts, based on the configured sending time.
    """
    # Instance of a class that encapsulates the email sending logic.
    email_notification = DeactivatedAccountNotificationEmail(
        emails=emails, activation_deadline=activation_deadline
    )

    # Sends the email and gets the count of successfully sent emails.
    try:
        sent_count: int = email_notification.send_with_error_handling()
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    # Returns the count of sent emails and the list of emails.
    return sent_count


def notify_expired_account_deletion() -> tuple[int, list[str]]:
    """
    Recovers emails from account who will be notified about the removal
    of their accounts from the system, for not activating them in a timely manner.
    After successful sending, these emails are removed.

    If there are no account to notify, returns -1.
    """
    # Recovers emails from account who will be notified.
    emails: list[str] = list(
        AccountsPendingDeletionNotificationModel.objects.values_list("email", flat=True)
    )

    if not emails:
        return (-1, [])

    # Instance of a class that encapsulates the email sending logic.
    email_notification = ExpiredAccountDeletionEmail(emails=emails)

    # Sends the email and gets the count of successfully sent emails.
    try:
        sent_count: int = email_notification.send_with_error_handling()
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    AccountsPendingDeletionNotificationModel.objects.all().delete()

    return (sent_count, emails)
