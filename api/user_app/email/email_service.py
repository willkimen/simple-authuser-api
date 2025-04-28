"""
This module contains functions for sending emails related to user actions, 
such as account changes and notifications. It handles the creation and 
sending of verification codes and notification messages to the user.
"""

import smtplib
from datetime import datetime

from user_app.constants.verification_code import (
    ACTIVATE_ACCOUNT_PREFIX,
    CHANGE_EMAIL_PREFIX,
    RESET_PASSWORD_PREFIX,
)
from user_app.email.email_classes import (
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
from user_app.models import (
    AccountActivationCodeModel,
    ChangeEmailCodeModel,
    ResetPasswordCodeModel,
    UsersPendingDeletionNotificationModel,
)


def send_email_change_code(actual_email: str, new_email: str) -> int:
    """
    Sends an email with a verification code to change the user's email address.

    This function generates a random verification code for changing the user's email,
    sends the code to the new email address, and stores the code.
    """

    # Creates code and verify if already exists in database
    code: str = ChangeEmailCodeModel.objects.verify_and_return_new_code(
        prefix=CHANGE_EMAIL_PREFIX
    )

    # Instance of a class that encapsulates the email sending logic.
    email = ChangeCodeEmail(actual_email=actual_email, new_email=new_email, code=code)

    # Sends the email and gets the count of successfully sent emails.
    try:
        sent_count: int = email.send_with_error_handling()
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    # Persists code in database.
    ChangeEmailCodeModel.objects.create(
        code=email.code, user_id=email.actual_email, new_email=email.new_email
    )
    # Removes all verification codes for a user, except the most recent one.
    ChangeEmailCodeModel.objects.keep_latest_code(email.actual_email)

    return sent_count


def send_account_activation_code(user_email: str) -> int:
    """
    Sends an account activation email to the user with a verification code.

    This function generates a random code for account activation, sends it to the
    user's email, and saves the code and email in the database. The activation code is
    used for verifying the user's email during the registration process.
    """

    # Creates code and verify if already exists in database
    code: str = AccountActivationCodeModel.objects.verify_and_return_new_code(
        prefix=ACTIVATE_ACCOUNT_PREFIX
    )

    # Instance of a class that encapsulates the email sending logic.
    email = ActivationCodeEmail(user_email=user_email, code=code)

    # Sends the email and gets the count of successfully sent emails.
    try:
        sent_count: int = email.send_with_error_handling()
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    # Persists code in database.
    AccountActivationCodeModel.objects.create(code=email.code, user_id=email.user_email)
    # Removes all verification codes for a user, except the most recent one.
    AccountActivationCodeModel.objects.keep_latest_code(email.user_email)

    return sent_count


def send_reset_password_code(user_email: str) -> int:
    """
    Sends a password reset code to the user's email address.

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
    email = ResetPasswordCodeEmail(user_email=user_email, code=code)

    # Sends the email and gets the count of successfully sent emails.
    try:
        sent_count: int = email.send_with_error_handling()
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    # Persists code in database.
    ResetPasswordCodeModel.objects.create(code=email.code, user_id=email.user_email)
    # Removes all verification codes for a user, except the most recent one.
    ResetPasswordCodeModel.objects.keep_latest_code(email.user_email)

    return sent_count


def notify_activated_account(user_email: str) -> int:
    """
    Sends a notification email to the user informing them that their account
    has been activated.
    """

    # Instance of a class that encapsulates the email sending logic.
    email = ActivationNotificationEmail(user_email=user_email)

    # Sends the email and gets the count of successfully sent emails.
    try:
        sent_count: int = email.send_with_error_handling()
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    return sent_count


def notify_changed_email(user_email: str) -> int:
    """
    Sends a notification email to the user informing them that their email address
    has been changed.
    """
    # Instance of a class that encapsulates the email sending logic.
    email = ChangeNotificationEmail(new_email=user_email)

    # Sends the email and gets the count of successfully sent emails.
    try:
        sent_count: int = email.send_with_error_handling()
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    return sent_count


def notify_reset_password(user_email: str) -> int:
    """
    Sends a notification email to the user informing them that their passoword
    has been reset.
    """
    # Instance of a class that encapsulates the email sending logic.
    email = PasswordResetNotificationEmail(user_email=user_email)

    # Sends the email and gets the count of successfully sent emails.
    try:
        sent_count: int = email.send_with_error_handling()
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    return sent_count


def notify_deleted_account(user_email: str) -> int:
    """
    Sends a notification email to the user informing them that their account
    has been deleted.
    """
    # Instance of a class that encapsulates the email sending logic.
    email = DeletedAccountNotificationEmail(user_email=user_email)

    # Sends the email and gets the count of successfully sent emails.
    try:
        sent_count: int = email.send_with_error_handling()
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    return sent_count


def notify_activation_account_reminder(
    emails: list[str], activation_deadline: datetime
) -> int:
    """
    Sends the reminder email to users who have not yet activated their
    accounts, based on the configured sending time.
    """
    # Instance of a class that encapsulates the email sending logic.
    email = DeactivatedAccountNotificationEmail(
        emails=emails, activation_deadline=activation_deadline
    )

    # Sends the email and gets the count of successfully sent emails.
    try:
        sent_count: int = email.send_with_error_handling()
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    # Returns the count of sent emails and the list of emails.
    return sent_count


def notify_expired_account_deletion() -> tuple[int, list[str]]:
    """
    Recovers emails from users who will be notified about the removal
    of their accounts from the system, for not activating them in a timely manner.
    After successful sending, these emails are removed.

    If there are no users to notify, returns -1.
    """
    # Recovers emails from users who will be notified.
    emails: list[str] = list(
        UsersPendingDeletionNotificationModel.objects.values_list("email", flat=True)
    )

    if not emails:
        return (-1, [])

    # Instance of a class that encapsulates the email sending logic.
    email = ExpiredAccountDeletionEmail(emails=emails)

    # Sends the email and gets the count of successfully sent emails.
    try:
        sent_count: int = email.send_with_error_handling()
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    UsersPendingDeletionNotificationModel.objects.all().delete()

    return (sent_count, emails)
