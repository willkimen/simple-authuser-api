"""
Test module for the expired tokens removal command.

This module contains automated tests that verify the functionality of the custom 
`remove_exp_token` command. The command is responsible for removing tokens with expired 
dates from the `ValidTokenModel` and `BlacklistTokenModel` models.
"""

from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone
from user_app.models import BlacklistTokenModel, ValidTokenModel


# ============== Tests ==================
@pytest.mark.django_db
def test_remove_exp_tokens(user):
    """
    Tests the expired tokens removal command.
    """
    # Persists tokens with expired dates
    token_data = {
        "user": user,
        "exp": timezone.now() - timedelta(days=1),
        "typ": "fake_typ",
    }

    valid_jti = ValidTokenModel.objects.create(jti="jti_fake_valid", **token_data).jti
    blacklisted_jti = BlacklistTokenModel.objects.create(
        jti="jti_fake_blacklisted", **token_data
    ).jti

    # Verify if tokens exist before removing them
    assert ValidTokenModel.objects.filter(jti=valid_jti).exists()
    assert BlacklistTokenModel.objects.filter(jti=blacklisted_jti).exists()

    # Call command to remove expired tokens
    call_command("remove_exp_token")

    # Verify if the tokens have been removed
    assert not ValidTokenModel.objects.filter(jti=valid_jti).exists()
    assert not BlacklistTokenModel.objects.filter(jti=blacklisted_jti).exists()
