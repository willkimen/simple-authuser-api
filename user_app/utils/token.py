from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.tokens import PasswordResetTokenGenerator


class UserActiveTokenGenerator(PasswordResetTokenGenerator):
    """
    Generates a token to verify if a user is active.

    This token generator is based on the PasswordResetTokenGenerator class,
    which will be used specifically for user registration confirmation.


    Methods:
        _make_hash_value(user, timestamp):
            Generates the hash value for the token using the user's ID,
            timestamp, is_active, and email.
    """

    def _make_hash_value(self, user: AbstractBaseUser, timestamp: int) -> str:
        """
        Creates the hash value for the token.

        Args:
          user (AbstractBaseUser): The user instance for which the token is generated.
            timestamp (int): The current timestamp.

        Returns:
            str: The generated hash value.
        """
        email_field = (
            user.get_email_field_name()
        )  # Gets the name of the user's email field
        email = (
            getattr(user, email_field, "") or ""
        )  # Gets the user's email value, or an empty string if no email exists
        return f"{user.id}{timestamp}{user.is_active}{email}"  # Returns the hash value composed of ID, timestamp, is_active, and email


# Instance of the user activity token generator
user_active_generate_token = UserActiveTokenGenerator()
