"""
Custom command to remove all codes with an expiration date earlier than 
the current date.

This command is used to clean expired codes from the following tables:
- `AccountActivationCodeModel`: Account activation codes.
- `ChangeEmailCodeModel`: Change email codes.
- `ResetPasswordCodeModel`: Reset password codes.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from user_app.models import (
    AccountActivationCodeModel,
    ChangeEmailCodeModel,
    ResetPasswordCodeModel,
)


class Command(BaseCommand):
    help = "Remove all codes with expired date."

    def handle(self, *args, **kwargs):
        now = timezone.now()
        AccountActivationCodeModel.objects.filter(expires_at__lt=now).delete()
        ChangeEmailCodeModel.objects.filter(expires_at__lt=now).delete()
        ResetPasswordCodeModel.objects.filter(expires_at__lt=now).delete()
