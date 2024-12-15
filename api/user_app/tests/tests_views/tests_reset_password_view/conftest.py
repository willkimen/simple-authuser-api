import pytest
from rest_framework.test import APIClient


# ============ Fixtures ================
@pytest.fixture
def client() -> APIClient:
    """
    This client is used to send HTTP requests in the tests.
    """
    return APIClient()
