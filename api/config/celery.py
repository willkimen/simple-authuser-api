import os

from celery import Celery
from user_app.constants.celery_constants import (
    EMAIL_QUEUE_NAME,
    REMOVE_EXPIRED_CODE_TOKEN_QUEUE_NAME,
)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.task_routes = {
    "user_app.tasks.task_remove_exp_code": {
        "queue": REMOVE_EXPIRED_CODE_TOKEN_QUEUE_NAME
    },
    "user_app.tasks.task_remove_exp_token": {
        "queue": REMOVE_EXPIRED_CODE_TOKEN_QUEUE_NAME
    },
    "user_app.tasks.task_send_activation_code_by_email": {"queue": EMAIL_QUEUE_NAME},
    "user_app.tasks.task_send_change_email_code_by_email": {"queue": EMAIL_QUEUE_NAME},
    "user_app.tasks.task_send_reset_password_code_by_email": {
        "queue": EMAIL_QUEUE_NAME
    },
}

app.autodiscover_tasks()
