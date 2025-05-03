from django.core.management.base import BaseCommand
from account_auth.periodic_tasks import create_periodic_task_for_notify_second_reminder


class Command(BaseCommand):
    help = "Creates a periodic task to send the second account activation reminder."

    def handle(self, *args, **kwargs) -> None:
        create_periodic_task_for_notify_second_reminder()
