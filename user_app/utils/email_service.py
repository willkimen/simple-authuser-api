import os
import smtplib

from django.contrib.auth.models import AbstractBaseUser
from django.core.mail import EmailMessage
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from ..utils.token import user_active_generate_token


def send_activation_email(user: AbstractBaseUser) -> None:
    """
    Sends an activation email to the user.

    Args:
        user (User): The user instance to whom the email will be sent.

    This function creates the content of the account activation email, including an activation link with a secure token.
    """
    email_subject = "Activate your account"  # Email subject
    uid = urlsafe_base64_encode(force_bytes(user.id))  # Encode the user ID in base64
    # Generate an activation token for the user
    token = user_active_generate_token.make_token(user)
    end_point = reverse("confirmation_register", kwargs={"id": uid, "token": token})

    activation_link = f"http://{os.environ.get('ENV_DOMAIN')}{end_point}"  # Create the activation link

    email_body = dedent(
        f"""
    Hi {user.first_name} {user.last_name},

    Please click the link below to activate your account:

    {activation_link}

    If you did not request this email, please ignore it.
    """
    )

    # Create the email messag
    email = EmailMessage(subject=email_subject, body=email_body, to=[user.email])
    try:
        email.send()
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
