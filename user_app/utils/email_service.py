import smtplib
from textwrap import dedent

from django.core.mail import EmailMessage

from user_app.constants.prefixes import ACTIVATE_ACCOUNT_PREFIX, CHANGE_EMAIL_PREFIX
from user_app.models import AccountActivationCodeModel, ChangeEmailCodeModel
from user_app.utils.random_code import generate_random_code


def __send_email_with_error_handling(email_message):
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


def send_change_email_code_by_email(old_email: str, new_email: str):
    email_subject = "Confirm your email address change"

    # Creates code and verify if already exists in database
    code = generate_random_code(prefix=CHANGE_EMAIL_PREFIX)
    while ChangeEmailCodeModel.objects.filter(code=code).exists():
        code = generate_random_code(prefix=CHANGE_EMAIL_PREFIX)

    email_body = dedent(
        f"""
    You requested to change your email from {old_email} to {new_email}.

    To confirm this change, please use the confirmation code below:

    {code}

    If you did not request this email change, please ignore this message. Your account will remain unchanged.
    """
    )

    email_message = EmailMessage(subject=email_subject, body=email_body, to=[new_email])

    try:
        __send_email_with_error_handling(email_message)
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    ChangeEmailCodeModel.objects.create(
        code=code,
        old_email=old_email,
        new_email=new_email,
    )


def send_activation_code_by_email(user_email: str) -> None:
    """
    Sends an activation email to the user.
    This function creates content with a random code to confirm the user's email address.
    The code will be persisted in the database, along with the user's email.
    """
    email_subject = "Confirm your email address"

    # Creates code and verify if already exists in database
    code = generate_random_code(prefix=ACTIVATE_ACCOUNT_PREFIX)
    while AccountActivationCodeModel.objects.filter(code=code).exists():
        code = generate_random_code(prefix=ACTIVATE_ACCOUNT_PREFIX)

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
        user_email=user_email,
    )
