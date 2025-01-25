import pytest
from django.conf import settings
from rest_framework.test import APIClient


# ============ Fixtures ================
@pytest.fixture
def client() -> APIClient:
    """
    This client is used to send HTTP requests in the tests.
    """
    return APIClient()


@pytest.fixture(scope="session", autouse=True)
def set_celery_test_settings():
    """
    Configures Celery tasks to run synchronously during tests.

    This fixture modifies two Celery settings:
    1. CELERY_TASK_ALWAYS_EAGER: Sets it to `True`, forcing tasks to execute
                                 synchronously within the current process.
    2. CELERY_TASK_EAGER_PROPAGATES: Sets it to `True`, ensuring that exceptions
                                     raised during task execution propagate
                                     to the tests.

    Scope:
    - This fixture has a session scope (scope="session") and
        is applied automatically to all tests (`autouse=True`).

    Usage:
    - This setup is useful for testing Celery task behavior
       without relying on an active worker or external queues.

    Obs:
    - If you are running worker containers, this may not be necessary
        if you want to run tasks asynchronously.
    """
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
