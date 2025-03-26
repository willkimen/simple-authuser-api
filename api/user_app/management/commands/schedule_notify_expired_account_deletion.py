from django.core.management.base import BaseCommand
from user_app.periodic_tasks import (
    create_periodic_task_for_notify_expired_account_deletion,
)


class Command(BaseCommand):
    help = "Persists the scheduling of the notify users about account deletion task"

    def handle(self, *args, **kwargs):
        create_periodic_task_for_notify_expired_account_deletion()
