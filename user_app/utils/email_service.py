import smtplib
from textwrap import dedent

from django.core.mail import EmailMessage

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
from user_app.utils.random_code import generate_random_code


def __send_email_with_error_handling(email_message: EmailMessage):
    """
    Sends an email and handles any SMTP-related errors.

    Args:
        email_message (EmailMessage): The email message to be sent.

    Raises:
        smtplib.SMTPConnectError: If there is a connection issue with the SMTP server.
        smtplib.SMTPAuthenticationError: If the authentication credentials for the
                                         SMTP server are incorrect.
        smtplib.SMTPSenderRefused: If the sender address is refused by the server.
        smtplib.SMTPRecipientsRefused: If all recipient addresses are refused by
                                       the server.
        smtplib.SMTPDataError: If the SMTP server rejects the message data.
        smtplib.SMTPResponseException: For generic SMTP response errors.
        smtplib.SMTPException: For any other SMTP-related errors.
    """
    try:
        email_message.send()
    except smtplib.SMTPConnectError as e:
        raise smtplib.SMTPConnectError(f"Failed to connect to the SMTP server: {e}")
    except smtplib.SMTPAuthenticationError as e:
        raise smtplib.SMTPAuthenticationError(
            f"SMTP authentication error. Check your username and password: {e}"
        )
    except smtplib.SMTPSenderRefused as e:
        raise smtplib.SMTPSenderRefused(
            f"The sender address was refused by the server: {e}"
        )
    except smtplib.SMTPRecipientsRefused as e:
        raise smtplib.SMTPRecipientsRefused(
            f"All recipient addresses were refused by the server: {e}"
        )
    except smtplib.SMTPDataError as e:
        raise smtplib.SMTPDataError(
            f"The SMTP server refused to accept the message data: {e}"
        )
    except smtplib.SMTPResponseException as e:
        raise smtplib.SMTPResponseException(
            e.smtp_code,
            e.smtp_error,
            f"SMTP server returned an error: {e.smtp_code} - {e.smtp_error}",
        )
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(f"An SMTP error occurred: {e}")


def send_change_email_code_by_email(actual_email: str, new_email: str):
    """
    Sends an email with a confirmation code to change the user's email address.

    This function generates a random confirmation code for changing the user's email,
    sends the code to the new email address, and stores the code.
    """
    email_subject = "Confirm your email address change"

    # Creates code and verify if already exists in database
    code: str = generate_random_code(prefix=CHANGE_EMAIL_PREFIX)
    while ChangeEmailCodeModel.objects.filter(code=code).exists():
        code: str = generate_random_code(prefix=CHANGE_EMAIL_PREFIX)

    email_body = dedent(
        f"""
    You requested to change your email from {actual_email} to {new_email}.

    To confirm this change, please use the confirmation code below:

    {code}

    If you did not request this email change, please ignore this message. Your account will remain unchanged.
    """
    )

    # Create the email message object
    email_message = EmailMessage(subject=email_subject, body=email_body, to=[new_email])

    try:
        __send_email_with_error_handling(email_message)
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    ChangeEmailCodeModel.objects.create(
        code=code,
        user_id=actual_email,
        new_email=new_email,
    )


def send_activation_code_by_email(user_email: str) -> None:
    """
    Sends an account activation email to the user with a confirmation code.

    This function generates a random code for account activation, sends it to the
    user's email, and saves the code and email in the database. The activation code is
    used for verifying the user's email during the registration process.
    """
    email_subject = "Confirm your email address"

    # Creates code and verify if already exists in database
    code: str = generate_random_code(prefix=ACTIVATE_ACCOUNT_PREFIX)
    while AccountActivationCodeModel.objects.filter(code=code).exists():
        code: str = generate_random_code(prefix=ACTIVATE_ACCOUNT_PREFIX)

    email_body = dedent(
        f"""
    Your confirmation code is below - enter it in your open browser window and we'll help you to sign in.

    {code}

    If you haven't requested this email, there's nothing to worry about - you can safely ignore it.
    """
    )

    # Create the email message object
    email_message = EmailMessage(
        subject=email_subject, body=email_body, to=[user_email]
    )

    try:
        __send_email_with_error_handling(email_message)
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    AccountActivationCodeModel.objects.create(
        code=code,
        user_id=user_email,
    )


def send_reset_password_code_by_email(user_email: str) -> None:
    """
    Sends a password reset code to the user's email address.

    This function generates a unique password reset code and sends it via email
    to the provided email address.
    The email contains the reset code and instructions. If an error occurs
    during the email sending process, the exception is raised and handled accordingly.
    """
    email_subject = "Reset Your Account Password"

    # Creates code and verify if already exists in database
    code: str = generate_random_code(prefix=RESET_PASSWORD_PREFIX)
    while ResetPasswordCodeModel.objects.filter(code=code).exists():
        code: str = generate_random_code(prefix=RESET_PASSWORD_PREFIX)

    email_body = dedent(
        f"""
    Your password reset code is below - enter it in your open browser window to reset your password.

    {code}

    If you haven't requested a password reset, there's nothing to worry about - you can safely ignore this email.
    """
    )

    # Create the email message object
    email_message = EmailMessage(
        subject=email_subject, body=email_body, to=[user_email]
    )

    try:
        __send_email_with_error_handling(email_message)
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    ResetPasswordCodeModel.objects.create(
        code=code,
        user_id=user_email,
    )
