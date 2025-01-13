import smtplib
from textwrap import dedent

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
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

MESSAGE_EXPIRED = (
    f"Please note that this code is valid for {settings.EXPIRATION_CODE_TIME_IN_HOURS} "
    "hours. After that, it will expire, and you'll need to request a new one."
)

MESSAGE_SAFELY_IGNORE = "If you haven't requested this email, you can safely ignore it."


def _verify_and_return_new_code(prefix: str) -> str:
    code: str = generate_random_code(prefix=prefix)
    while ChangeEmailCodeModel.objects.filter(code=code).exists():
        code: str = generate_random_code(prefix=prefix)
    return code


def _email_multi_alternatives_factory(
    subject: str, body: str, to: str, html_body: str
) -> EmailMultiAlternatives:
    email_multi = EmailMultiAlternatives(subject=subject, body=body, to=[to])
    email_multi.content_subtype = "html"  # Make the email HTML-friendly
    email_multi.attach_alternative(html_body, "text/html")
    return email_multi


def __send_email_with_error_handling(email_multi: EmailMultiAlternatives) -> int:
    """
    Sends an email and handles any SMTP-related errors.

    Args:
        email_multi (EmailMultiAlternatives): The email message to be sent.

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
        sent_count: int = email_multi.send()
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

    return sent_count


def send_change_email_code_by_email(actual_email: str, new_email: str) -> int:
    """
    Sends an email with a confirmation code to change the user's email address.

    This function generates a random confirmation code for changing the user's email,
    sends the code to the new email address, and stores the code.
    """
    subject = "Confirm your email address change"

    # Creates code and verify if already exists in database
    code: str = _verify_and_return_new_code(prefix=CHANGE_EMAIL_PREFIX)

    body = dedent(
        f"""
    You requested to change your email from {actual_email} to {new_email}.

    To confirm this change, please use the confirmation code below:

    {code}

    {MESSAGE_EXPIRED}

    {MESSAGE_SAFELY_IGNORE}
    """
    )

    html_body = dedent(
        f"""
        <p>You requested to change your email from <strong>{actual_email}</strong> to 
        <strong>{new_email}</strong>.</p>
        <p>To confirm this change, please use the confirmation code below:</p>
        <h2>{code}</h2>
        <p>{MESSAGE_EXPIRED}</p>
        <p>{MESSAGE_SAFELY_IGNORE}</p>
        """
    )

    # Create the email message object
    email_multi = _email_multi_alternatives_factory(
        subject=subject, body=body, to=new_email, html_body=html_body
    )

    try:
        sent_count: int = __send_email_with_error_handling(email_multi)
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    ChangeEmailCodeModel.objects.create(
        code=code, user_id=actual_email, new_email=new_email
    )

    return sent_count


def send_activation_code_by_email(user_email: str) -> None:
    """
    Sends an account activation email to the user with a confirmation code.

    This function generates a random code for account activation, sends it to the
    user's email, and saves the code and email in the database. The activation code is
    used for verifying the user's email during the registration process.
    """
    subject = "Confirm your email address"

    # Creates code and verify if already exists in database
    code: str = _verify_and_return_new_code(prefix=ACTIVATE_ACCOUNT_PREFIX)

    body = dedent(
        f"""
        Your confirmation code is below:

        {code}

        To complete your registration, please visit the following link and submit the
        code:
        {settings.CONFIRMATION_LINK}

        Note: You have 7 days to activate your account. If you do not activate it within
        this period, your account will be removed.

        {MESSAGE_EXPIRED}

        {MESSAGE_SAFELY_IGNORE}
        """
    )

    html_body = dedent(
        f"""
        <p>Your confirmation code is below:</p>
        <h2>{code}</h2>
        <p>To complete your registration, please visit the following link and submit
        the code:</p>
        <a href="{settings.CONFIRMATION_LINK}">Activate Account</a>
        <p><strong>Note:</strong> You have 7 days to activate your account. If you do
        not activate it within this period, your account will be removed.</p>
        <p>{MESSAGE_EXPIRED}</p>
        <p>{MESSAGE_SAFELY_IGNORE}</p>
        """
    )

    # Create the email message object
    email_multi = _email_multi_alternatives_factory(
        subject=subject, body=body, to=user_email, html_body=html_body
    )

    try:
        sent_count: int = __send_email_with_error_handling(email_multi)
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    AccountActivationCodeModel.objects.create(code=code, user_id=user_email)

    return sent_count


def send_reset_password_code_by_email(user_email: str) -> None:
    """
    Sends a password reset code to the user's email address.

    This function generates a unique password reset code and sends it via email
    to the provided email address.
    The email contains the reset code and instructions. If an error occurs
    during the email sending process, the exception is raised and handled accordingly.
    """
    subject = "Reset Your Account Password"

    # Creates code and verify if already exists in database
    code: str = _verify_and_return_new_code(prefix=RESET_PASSWORD_PREFIX)

    body = dedent(
        f"""
        Your password reset code is below:

        {code}

        To reset your password, please visit the following link and submit the code:
        {settings.RESET_LINK}

        {MESSAGE_EXPIRED}

        {MESSAGE_SAFELY_IGNORE}
        """
    )

    html_body = dedent(
        f"""
        <p>Your password reset code is below:</p>
        <h2>{code}</h2>
        <p>To reset your password, please visit the following link and submit 
        the code:</p>
        <a href="{settings.RESET_LINK}">Reset Password</a>
        <p>{MESSAGE_EXPIRED}</p>
        <p>{MESSAGE_SAFELY_IGNORE}</p>
        """
    )

    # Create the email message object
    email_multi = _email_multi_alternatives_factory(
        subject=subject, body=body, to=user_email, html_body=html_body
    )

    try:
        sent_count: int = __send_email_with_error_handling(email_multi)
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(str(e))

    ResetPasswordCodeModel.objects.create(code=code, user_id=user_email)

    return sent_count
