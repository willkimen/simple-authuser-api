"""
Test file for the asynchronous task `task_remove_exp_token`.
"""

from datetime import timedelta

import pytest
from celery import states
from celery.result import EagerResult
from django.utils import timezone
from account_auth.models import BlacklistTokenModel, ValidTokenModel
from account_auth.tasks import task_remove_exp_token


@pytest.mark.django_db
def test_task_should_remove_exp_token(account):
    """
    fully tests the task's functionality, confirming
       that expired tokens are removed from the database.
    """
    # Persists tokens with expired dates
    token_data = {
        "account": account,
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
    result: EagerResult = task_remove_exp_token.apply()

    assert result.status == states.SUCCESS
    # Verify if the tokens have been removed
    assert not ValidTokenModel.objects.filter(jti=valid_jti).exists()
    assert not BlacklistTokenModel.objects.filter(jti=blacklisted_jti).exists()
