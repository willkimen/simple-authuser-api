from django.core.management.base import BaseCommand
from user_app.periodic_tasks import create_periodic_task_for_expired_tokens_removal


class Command(BaseCommand):
    help = "Persists the scheduling of the expired tokens removal task"

    def handle(self, *args, **kwargs):
        create_periodic_task_for_expired_tokens_removal()
