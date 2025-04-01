from django.core.management.base import BaseCommand
from user_app.periodic_tasks import create_periodic_task_for_notify_first_reminder


class Command(BaseCommand):
    help = "Creates a periodic task to send the first account activation reminder."

    def handle(self, *args, **kwargs) -> None:
        create_periodic_task_for_notify_first_reminder()
