from datetime import datetime

from django.conf import settings
from django.db import models
from django.utils import timezone


class TokenBaseModel(models.Model):
    """
    Abstract base model representing a JWT token.

    This model stores the `jti` (JWT ID) and `exp` (expiration time) of a token.
    The expiration field is managed to ensure it's stored as a `DateTimeField`,
    converting from an integer timestamp if necessary.


    Attributes:
        TYPE_TOKEN_CHOICES (list): Choices for the type of token.

    Fields:
        typ (CharField): The type of the token, which can be
                         either 'access' or 'refresh'. This field is limited
                         to the choices defined in `TYPE_TOKEN_CHOICES`.
    Methods:
        save: Overrides the default save method to handle the `exp` field conversion.
    """

    TYPE_TOKEN_CHOICES = [
        ("access", "access"),
        ("refresh", "refresh"),
    ]

    jti = models.CharField(max_length=255)
    exp = models.DateTimeField()
    typ = models.CharField(max_length=10, choices=TYPE_TOKEN_CHOICES)

    def save(self, *args, **kwargs) -> None:
        """
        Override the default save method to handle the expiration field.

        If the expiration field (`exp`) is provided as an integer timestamp,
        it is converted to a datetime object before saving to the database.
        This ensures that the expiration time is correctly stored as a `DateTimeField`.

        Calls the parent class's save method to perform the actual save operation.
        """
        if isinstance(self.exp, int):
            self.exp: datetime = timezone.make_aware(datetime.fromtimestamp(self.exp))
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class BlacklistTokenModel(TokenBaseModel):
    """
    Represents a model for storing blacklisted JWTs (JSON Web Tokens).
    This is used to keep track of tokens
    that should no longer be accepted by the system.

    Fields:
        user (ForeignKey): A foreign key relationship to the default user defined in
                           settings.AUTH_USER_MODEL, representing the user that owns
                           this token.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=False,
        related_name="blacklist_tokens",
        db_column="uid",
    )

    class Meta:
        db_table = "blacklist_token"
        verbose_name = "blacklist token"


class ValidTokenModel(TokenBaseModel):
    """
    Represents a model for storing valid tokens.

    Fields:
        user (ForeignKey): A foreign key relationship to the default user defined in
                           settings.AUTH_USER_MODEL, representing the user that owns
                           this token.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=False,
        related_name="valid_tokens",
        db_column="uid",
    )

    class Meta:
        db_table = "valid_token"
        verbose_name = "valid token"
