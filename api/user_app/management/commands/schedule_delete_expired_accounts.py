from django.core.management.base import BaseCommand
from user_app.periodic_tasks import create_periodic_task_for_delete_expired_accounts


class Command(BaseCommand):
    help = "Persists the scheduling of the delete expired accounts task"

    def handle(self, *args, **kwargs):
        create_periodic_task_for_delete_expired_accounts()
