import smtplib
from textwrap import dedent

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

EXPIRED_MESSAGE = (
    f"Please note that this code is valid for {settings.EXPIRATION_CODE_TIME_IN_HOURS} "
    "hours. After that, it will expire, and you'll need to request a new one."
)

SAFELY_IGNORE_MESSAGE = "If you haven't requested this email, you can safely ignore it."

LOGIN_MESSAGE = "You can now log in using the link below:\n" f"{settings.LOGIN_LINK}"

CONTACT_SUPPORT_MESSAGE = (
    "If you did not this request, please contact our support team immediately."
)


class EmailBase(EmailMultiAlternatives):
    """
    Base class for sending emails with SMTP error handling.

    This class provides an enhanced method for sending emails with SMTP
    error handling. It attempts to send an email and raises specific exceptions
    based on the type of SMTP error encountered.
    """

    def send_with_error_handling(self) -> int:
        """
        Sends an email and handles any SMTP-related errors.
        Raises:
            smtplib.SMTPConnectError: If there is connection issue with the SMTP server.
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
            sent_count: int = self.send()
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


class ActivationCodeEmail(EmailBase):
    """
    Sends an account activation email containing a verification code.

    This class is responsible for sending an email with a verification code
    to activate a user's account. The email is sent in both plain text and HTML formats.
    """

    def __init__(self, user_email: str, code: str = None, **kwargs):
        self.user_email = user_email
        self.code = code
        self.subject = "Confirm your email address"
        self.body = dedent(
            f"""
            Your verification code is below:

            {self.code}

            To complete your registration, please visit the following link and submit 
            the code:
            {settings.CONFIRMATION_LINK}

            Note: You have 7 days to activate your account. If you do not activate it 
            within this period, your account will be removed.

            {EXPIRED_MESSAGE}

            {SAFELY_IGNORE_MESSAGE}
            """
        )

        self.html_body = dedent(
            f"""
            <p>Your verification code is below:</p>
            <h2>{self.code}</h2>
            <p>To complete your registration, please visit the following link and submit
            the code:</p>
            <a href="{settings.CONFIRMATION_LINK}">Activate Account</a>
            <p><strong>Note:</strong> You have 7 days to activate your account. If you do
            not activate it within this period, your account will be removed.</p>
            <p>{EXPIRED_MESSAGE}</p>
            <p>{SAFELY_IGNORE_MESSAGE}</p>
            """
        )

        super().__init__(
            subject=self.subject, body=self.body, to=[self.user_email], **kwargs
        )

        self.attach_alternative(self.html_body, "text/html")


class ActivationNotificationEmail(EmailBase):
    """
    Sends an account activation notification email.

    This class is responsible for sending an email to inform the user that
    their account has been successfully activated. The email is sent in both
    plain text and HTML formats and includes a login link and support contact
    information.
    """

    def __init__(self, user_email: str, **kwargs):
        self.user_email = user_email
        self.subject = "Your account has been activated"
        self.body = dedent(
            f"""
            Your account has been successfully activated.

            {LOGIN_MESSAGE}

            {CONTACT_SUPPORT_MESSAGE}
            """
        )

        self.html_body = dedent(
            f"""
            <p>Your account has been successfully activated.</p>
            <p>You can now <a href="{settings.LOGIN_LINK}">log in</a> using the link below:</p>
            <a href="{settings.LOGIN_LINK}">Login</a>
            <p>{CONTACT_SUPPORT_MESSAGE}</p>
            """
        )

        super().__init__(
            subject=self.subject, body=self.body, to=[self.user_email], **kwargs
        )

        self.attach_alternative(self.html_body, "text/html")


class ChangeCodeEmail(EmailBase):
    """
    Sends a verification email for changing the user's email address.

    This class sends an email to the user containing a verification code
    for changing their email address. The email informs the user about
    the request to change the email from the current address to the new one,
    and provides the verification code that the user needs to use to verification
    the change.
    """

    def __init__(self, actual_email: str, new_email: str, code: str, **kwargs):
        self.new_email = new_email
        self.actual_email = actual_email
        self.code = code
        self.subject = "Confirm your email address change"
        self.body = dedent(
            f"""
        You requested to change your email from {self.actual_email} to {self.new_email}.

        To confirm this change, please use the verification code below:

        {self.code}

        {EXPIRED_MESSAGE}

        {SAFELY_IGNORE_MESSAGE}
        """
        )

        self.html_body = dedent(
            f"""
            <p>You requested to change your email from <strong>{self.actual_email}</strong> to 
            <strong>{self.new_email}</strong>.</p>
            <p>To confirm this change, please use the verification code below:</p>
            <h2>{self.code}</h2>
            <p>{EXPIRED_MESSAGE}</p>
            <p>{SAFELY_IGNORE_MESSAGE}</p>
            """
        )

        super().__init__(
            subject=self.subject, body=self.body, to=[self.new_email], **kwargs
        )
        self.attach_alternative(self.html_body, "text/html")


class ChangeNotificationEmail(EmailBase):
    """
    Sends an email notification confirming the successful change of the
    user's email address.

    This class sends an email to the user notifying them that their email address
    has been successfully changed. The email includes a login link for the user to
    access their account with the new email address.
    """

    def __init__(self, new_email: str, **kwargs):
        self.new_email = new_email
        self.subject = "Your email address has been changed"
        self.body = dedent(
            f"""
            Your old email address has been successfully changed.

            {LOGIN_MESSAGE}

            {CONTACT_SUPPORT_MESSAGE}
            """
        )

        self.html_body = dedent(
            f"""
            <p>Your old email address has been successfully changed.</p>
            <p>You can now <a href="{settings.LOGIN_LINK}">log in</a> using the link below:</p>
            <a href="{settings.LOGIN_LINK}">Login</a>
            <p>{CONTACT_SUPPORT_MESSAGE}</p>
            """
        )

        super().__init__(
            subject=self.subject, body=self.body, to=[self.new_email], **kwargs
        )

        self.attach_alternative(self.html_body, "text/html")


class ResetPasswordCodeEmail(EmailBase):
    """
    Sends a password reset email with a verification code to the user's email address.

    This class sends an email containing a verification code to the user's email
    address to initiate the password reset process. The user will need to visit a
    provided link and submit the verification code to reset their password.
    """

    def __init__(self, user_email: str, code: str, **kwargs):
        self.user_email = user_email
        self.code = code
        self.subject = "Reset Your Account Password"
        self.body = dedent(
            f"""
            Your password reset code is below:

            {self.code}

            To reset your password, please visit the following link and submit the code:
            {settings.RESET_LINK}

            {EXPIRED_MESSAGE}

            {SAFELY_IGNORE_MESSAGE}
            """
        )

        self.html_body = dedent(
            f"""
            <p>Your password reset code is below:</p>
            <h2>{self.code}</h2>
            <p>To reset your password, please visit the following link and submit 
            the code:</p>
            <a href="{settings.RESET_LINK}">Reset Password</a>
            <p>{EXPIRED_MESSAGE}</p>
            <p>{SAFELY_IGNORE_MESSAGE}</p>
            """
        )

        super().__init__(
            subject=self.subject, body=self.body, to=[self.user_email], **kwargs
        )

        self.attach_alternative(self.html_body, "text/html")


class PasswordResetNotificationEmail(EmailBase):
    """
    Sends a notification email to inform the user that their password has been
    reset successfully.

    This class sends an email notifying the user that their password has been
    successfully reset.
    The user will be informed that they can now log in using the new password.
    The email provides a link to the login page and includes a safety message
    in case the reset was not requested by the user.
    """

    def __init__(self, user_email: str, **kwargs):
        self.user_email = user_email
        self.subject = "Your Password Has Been Reset"
        self.body = dedent(
            f"""
            Your password has been successfully reset.

            {LOGIN_MESSAGE}

            {SAFELY_IGNORE_MESSAGE}
            """
        )

        self.html_body = dedent(
            f"""
            <p>Your password has been successfully reset.</p>
            <p>You can now <a href="{settings.LOGIN_LINK}">log in</a> using the link below:</p>
            <a href="{settings.LOGIN_LINK}">Login</a>
            <p>{SAFELY_IGNORE_MESSAGE}</p>
            """
        )

        super().__init__(
            subject=self.subject, body=self.body, to=[self.user_email], **kwargs
        )

        self.attach_alternative(self.html_body, "text/html")
