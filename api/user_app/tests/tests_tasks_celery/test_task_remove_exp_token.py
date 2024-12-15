"""
Test file for the asynchronous task `task_remove_exp_token`.
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from user_app.models import BlacklistTokenModel, ValidTokenModel
from user_app.tasks import task_remove_exp_token


@pytest.mark.django_db
@patch("user_app.tasks.call_command")
def test_task_executes_remove_exp_token_command(mock_call_command):
    """
    Ensures the `remove_exp_token` command is called during the task execution.
    """
    task_remove_exp_token()
    mock_call_command.assert_called_once_with("remove_exp_token")


@pytest.mark.django_db
def test_task_should_remove_exp_token(user):
    """
    fully tests the task's functionality, confirming
       that expired tokens are removed from the database.
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
    task_remove_exp_token()

    # Verify if the tokens have been removed
    assert not ValidTokenModel.objects.filter(jti=valid_jti).exists()
    assert not BlacklistTokenModel.objects.filter(jti=blacklisted_jti).exists()
