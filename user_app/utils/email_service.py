import threading

from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpRequest
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from ..utils.token import user_active_generate_token


class EmailThread(threading.Thread):
    """
    Class to send email in a new thread.

    Args:
        email (EmailMessage): The email instance to be sent.

    Methods:
        run(): Sends the email.
    """

    def __init__(self, email: EmailMessage) -> None:
        super().__init__()
        self.email = email

    def run(self) -> None:
        """
        Sends the email when the thread is started.
        """
        self.email.send()


def send_activation_email(user: User, request: HttpRequest) -> None:
    """
    Sends an activation email to the user.

    Args:
        user (User): The user instance to whom the email will be sent.
        request (HttpRequest): The current request instance to get the current site.

    This function creates the content of the account activation email, including an activation link with a secure token.
    The email is then sent in a new thread to avoid blocking the main process.
    """
    current_site = get_current_site(request)  # Get the current site from the request
    email_subject = "Activate your account"  # Email subject
    uid = urlsafe_base64_encode(
        force_bytes(user.id)
    )  # Encode the user ID in base64
    token = user_active_generate_token.make_token(
        user
    )  # Generate an activation token for the user
    end_point = reverse("confirmation_register", kwargs={"id": uid, "token": token})

    activation_link = (
        f"http://{current_site.domain}/api/v1/{end_point}"  # Create the activation link
    )

    email_body = f"""
    Hi {user.first_name} {user.last_name},

    Please click the link below to activate your account:

    {activation_link}

    If you did not request this email, please ignore it.
    """

    email = EmailMessage(
        subject=email_subject, body=email_body, to=[user.email]
    )  # Create the email message
    email_thread = EmailThread(email)  # Create a new thread to send the email
    email_thread.start()  # Start the thread to send the email
