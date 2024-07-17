import smtplib
from textwrap import dedent

from django.contrib.auth.models import AbstractBaseUser
from django.core.mail import EmailMessage

from ..models import ConfirmationCode
from .random_code import generate_random_code


def send_email_for_account_activation(user_email: str) -> None:
    """
    Sends an activation email to the user.
    This function creates content with a random code to confirm the user's email address.
    The code will be persisted in the database, along with the user's email.
    """
    email_subject = "Confirm your email address"

    # Creates confirmation code and verify if already exists in database
    confirmation_code = generate_random_code()
    while ConfirmationCode.objects.exists(code=confirmation_code):
        confirmation_code = generate_random_code()

    email_body = dedent(
        f"""
    Your confirmation code is below - enter it in your open browser window and we'll help you to sign in.

    {confirmation_code}

    If you haven't requested this email, there's nothing to worry about - you can safely ignore it.
    """
    )

    # Create the email message object
    email_message = EmailMessage(
        subject=email_subject, body=email_body, to=[user_email]
    )
    try:
        email_message.send()
        # Persists code in the database
        ConfirmationCode.objects.create(
            code=confirmation_code,
            user_email=user_email,
            type_code="registration_email_confirmation",
        )
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
