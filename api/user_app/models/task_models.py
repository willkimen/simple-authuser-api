"""
Module responsible for storing information about Celery tasks.

Currently defines a model for recording tasks that failed during execution,
including details such as task name, arguments, exception, and traceback.
It can be expanded in the future to include other types of task-related information.
"""

from celery import Task
from config.celery import app
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models


class FailedTaskModel(models.Model):
    """
    Model for storing information about failed Celery tasks.

    It records the task name, ID, arguments, exception details, and traceback.
    Also includes a method to retry the failed task.
    """

    task_name = models.CharField(max_length=255)
    task_id = models.CharField(max_length=255, blank=True, null=True)
    args = models.JSONField(encoder=DjangoJSONEncoder)
    kwargs = models.JSONField(encoder=DjangoJSONEncoder)
    exception = models.TextField(blank=True, null=True)
    traceback = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.task_name} failed at {self.created_at}"

    class Meta:
        db_table = "failed_task"
        verbose_name = "Failed Task"
        verbose_name_plural = "Failed Tasks"

    def retry(self) -> None:
        """
        Retrieves the associated Celery task and attempts to re-execute it.

        This method looks up the task by its recorded name, retrieves the original
        arguments and keyword arguments, and asynchronously re-executes the task
        using `delay`. After rescheduling the task, the failure record is deleted
        from the database.

        This method is especially useful in the Django Admin panel, where
        administrators can manually select and retry failed tasks through a
        custom action.
        """
        task: Task | None = app.tasks.get(self.task_name)
        if task is not None:
            task.delay(*tuple(self.args), **self.kwargs)
            self.delete()
