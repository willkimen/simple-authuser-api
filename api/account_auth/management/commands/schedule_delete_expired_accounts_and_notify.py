from django.core.management.base import BaseCommand
from account_auth.periodic_tasks import create_periodic_task_for_delete_and_notify


class Command(BaseCommand):
    help = "Persists the scheduling of the delete and notify expired accounts task"

    def handle(self, *args, **kwargs) -> None:
        create_periodic_task_for_delete_and_notify()
