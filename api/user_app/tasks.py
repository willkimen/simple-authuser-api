"""
Asynchronous tasks using Celery to execute commands for removing expired data.

Description:
This module defines tasks that use Celery to execute Django management commands, 
allowing the removal of expired records asynchronously and on a scheduled basis.

Usage:
These tasks can be scheduled or called directly through the Celery system 
to ensure that expired records are automatically removed in the background.

Example configuration for scheduling tasks:
- Use a scheduler such as `Celery Beat` to execute these tasks at regular intervals.
"""

from celery import shared_task
from django.core.management import call_command


@shared_task
def task_remove_exp_code():
    """
    Executes the `remove_exp_code` command to remove expired account activation codes,
    email change codes, and password reset codes.
    """
    call_command("remove_exp_code")


@shared_task
def task_remove_exp_token():
    """
    Executes the `remove_exp_token` command to remove expired validation tokens and
    tokens in the blacklist.
    """
    call_command("remove_exp_token")
