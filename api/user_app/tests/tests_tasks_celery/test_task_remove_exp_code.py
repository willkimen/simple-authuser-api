"""
Test file for the asynchronous task `task_remove_exp_code`.
"""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from user_app.models import (
    AccountActivationCodeModel,
    ChangeEmailCodeModel,
    ResetPasswordCodeModel,
)
from user_app.tasks import task_remove_exp_code


@pytest.mark.django_db
@patch("user_app.tasks.call_command")
def test_task_executes_remove_exp_code_command(mock_call_command):
    """
    Ensures the `remove_exp_code` command is called during the task execution.
    """
    task_remove_exp_code()
    mock_call_command.assert_called_once_with("remove_exp_code")


@pytest.mark.django_db
def test_task_should_remove_exp_code(user):
    """
    fully tests the task's functionality, confirming
       that expired codes are removed from the database.
    """

    # Persists codes with expired dates
    code_data = {"user": user, "expires_at": timezone.now() - timedelta(days=1)}
    activation_code = AccountActivationCodeModel.objects.create(**code_data).code
    change_code = ChangeEmailCodeModel.objects.create(**code_data).code
    reset_code = ResetPasswordCodeModel.objects.create(**code_data).code

    # Verify if codes exist before removing them
    assert ChangeEmailCodeModel.objects.filter(code=change_code).exists()
    assert AccountActivationCodeModel.objects.filter(code=activation_code).exists()
    assert ResetPasswordCodeModel.objects.filter(code=reset_code).exists()

    task_remove_exp_code()

    # Verify if the codes have been removed
    assert not ChangeEmailCodeModel.objects.filter(code=change_code).exists()
    assert not AccountActivationCodeModel.objects.filter(code=activation_code).exists()
    assert not ResetPasswordCodeModel.objects.filter(code=reset_code).exists()
