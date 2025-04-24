import pytest
from rest_framework.test import APIClient


# ================= Fixtures ===============
@pytest.fixture
def client() -> APIClient:
    """Returns an API client to make requests."""

    return APIClient()
