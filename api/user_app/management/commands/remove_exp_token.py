"""
Custom command to remove all tokens with an expiration date earlier than 
the current date.

This command is used to clean expired tokens from the following tables:
- `ValidTokenModel`: Valid tokens.
- `BlacklistTokenModel`: Blacklisted tokens.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from user_app.models import BlacklistTokenModel, ValidTokenModel


class Command(BaseCommand):
    help = "Remove all tokens with expired date."

    def handle(self, *args, **kwargs):
        now = timezone.now()
        ValidTokenModel.objects.filter(exp__lt=now).delete()
        BlacklistTokenModel.objects.filter(exp__lt=now).delete()
