import smtplib

from user_app.constants.prefixes import (
    ACTIVATE_ACCOUNT_PREFIX,
    CHANGE_EMAIL_PREFIX,
    RESET_PASSWORD_PREFIX,
)
from user_app.models import (
    AccountActivationCodeModel,
    ChangeEmailCodeModel,
    ResetPasswordCodeModel,
)
from user_app.utils.email_classes import (
    ActivationCodeEmail,
    ChangeCodeEmail,
    ResetPasswordCodeEmail,
)


def send_change_email_code_by_email(actual_email: str, new_email: str) -> int:
    """
    Sends an email with a confirmation code to change the user's email address.

    This function generates a random confirmation code for changing the user's email,
    sends the code to the new email address, and stores the code.
    """

    # Creates code and verify if already exists in database
    code: str = ChangeEmailCodeModel.objects.verify_and_return_new_code(
        prefix=CHANGE_EMAIL_PREFIX
    )

    email = ChangeCodeEmail(actual_email=actual_email, new_email=new_email, code=code)

    try:
        sent_count: int = email.send_with_error_handling()
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    # Persists code in database.
    ChangeEmailCodeModel.objects.create(
        code=email.code, user_id=email.actual_email, new_email=email.new_email
    )
    # Removes all confirmation codes for a user, except the most recent one.
    ChangeEmailCodeModel.objects.keep_latest_code(email.actual_email)

    return sent_count


def send_activation_code_by_email(user_email: str) -> int:
    """
    Sends an account activation email to the user with a confirmation code.

    This function generates a random code for account activation, sends it to the
    user's email, and saves the code and email in the database. The activation code is
    used for verifying the user's email during the registration process.
    """

    # Creates code and verify if already exists in database
    code: str = AccountActivationCodeModel.objects.verify_and_return_new_code(
        prefix=ACTIVATE_ACCOUNT_PREFIX
    )

    email = ActivationCodeEmail(user_email=user_email, code=code)

    try:
        sent_count: int = email.send_with_error_handling()
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    # Persists code in database.
    AccountActivationCodeModel.objects.create(code=email.code, user_id=email.user_email)
    # Removes all confirmation codes for a user, except the most recent one.
    AccountActivationCodeModel.objects.keep_latest_code(email.user_email)

    return sent_count


def send_reset_password_code_by_email(user_email: str) -> int:
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

    email = ResetPasswordCodeEmail(user_email=user_email, code=code)

    try:
        sent_count: int = email.send_with_error_handling()
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    # Persists code in database.
    ResetPasswordCodeModel.objects.create(code=email.code, user_id=email.user_email)
    # Removes all confirmation codes for a user, except the most recent one.
    ResetPasswordCodeModel.objects.keep_latest_code(email.user_email)

    return sent_count
