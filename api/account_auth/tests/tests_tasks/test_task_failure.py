import pytest
from account_auth.models import FailedTaskModel
from account_auth.tasks import TaskFailure


@pytest.mark.django_db
def test_task_on_failure_creates_failed_task_record():
    task = TaskFailure()
    task.name = "test_task_name"

    exc = ValueError("Test exception occurred")
    task_id = "test-task-id-123"
    args = [1, 2, 3]
    kwargs = {"key1": "value1", "key2": 2}

    class MockEInfo:
        traceback = "Simulated traceback for testing purposes"

    einfo = MockEInfo()

    task.on_failure(exc, task_id, args, kwargs, einfo)
    failed_task = FailedTaskModel.objects.get(task_id=task_id)

    assert failed_task.task_name == "test_task_name"
    assert failed_task.task_id == task_id
    assert failed_task.args == args
    assert failed_task.kwargs == kwargs
    assert failed_task.exception == str(exc)
    assert failed_task.traceback == einfo.traceback
