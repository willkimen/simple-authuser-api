from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from user_app.constants import http_response
from user_app.tests.constants import (
    ALLOW_REQUEST_FUNCTION_TO_PATCH,
    RESET_PASSWORD_VIEWS_MODULE_PATH,
    Account,
)

# =========== Objects and constants ==============
url: str = reverse("request_reset_password_code")
ACCOUNT_EMAIL = "fakeemail@email.com"
NON_EXISTENT_EMAIL = "nonexistent@email.com"


# ============ Fixtures ================
@pytest.fixture
def deactivate_account():
    """
    Fixture to create and return a deactivated Account object.
    """
    return Account.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email=ACCOUNT_EMAIL,
        password="1234@!AA",
        is_active=False,
    )


@pytest.fixture
def activate_account():
    """
    Fixture to create and return an activated Account object.
    """
    return Account.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email=ACCOUNT_EMAIL,
        password="1234@!AA",
        is_active=True,
    )


# ============ Tests ================
@pytest.mark.django_db
@patch(
    f"{RESET_PASSWORD_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_does_not_send_code_when_non_existent_email_in_database(
    allow_request_function_mock: MagicMock, client: APIClient
):
    """
    Tests that the system does not send a password reset code when the provided email
    is not found in the database.
    """
    expected_detail_message = http_response.ACCOUNT_NOT_FOUND["detail"]
    expected_code = http_response.ACCOUNT_NOT_FOUND["code"]
    expected_status_code = status.HTTP_404_NOT_FOUND

    actual_response = client.post(
        url, data={"email": NON_EXISTENT_EMAIL}, format="json"
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
@patch(
    f"{RESET_PASSWORD_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_does_not_send_code_when_deactivate_account(
    allow_request_function_mock: MagicMock, client: APIClient, deactivate_account
):
    """
    Tests that the system does not send a password reset code when the account is
    deactivated.
    """
    expected_detail_message = http_response.ACCOUNT_NOT_ACTIVATED["detail"]
    expected_code = http_response.ACCOUNT_NOT_ACTIVATED["code"]
    expected_status_code = status.HTTP_403_FORBIDDEN

    actual_response = client.post(
        url, data={"email": deactivate_account.email}, format="json"
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
def test_does_not_send_code_when_request_limit_is_reached(client: APIClient):
    """
    Tests that the system prevents sending the password reset code when the request rate
    limit has been reached.
    """
    expected_status_code = status.HTTP_429_TOO_MANY_REQUESTS
    expected_detail_message = "Request was throttled."
    expected_code = "throttled"
    limit_exceeded = 6

    # Simulate multiple POST requests to exceed the rate limit
    for _ in range(limit_exceeded):
        actual_response = client.post(url)

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message in actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]


@pytest.mark.django_db
@patch(
    f"{RESET_PASSWORD_VIEWS_MODULE_PATH}.{ALLOW_REQUEST_FUNCTION_TO_PATCH}",
    return_value=True,
)
def test_sends_the_code_to_the_account_email_successfully(
    allow_request_function_mock: MagicMock, client: APIClient, activate_account
):
    """
    Tests that the system successfully sends the password reset code to the account's email
    when the account is found and active.
    """
    expected_detail_message = http_response.EMAIL_SEND_TO_ACCOUNT_SUCCESSFULLY["detail"]
    expected_code = http_response.EMAIL_SEND_TO_ACCOUNT_SUCCESSFULLY["code"]
    expected_status_code = status.HTTP_200_OK

    actual_response = client.post(
        url, data={"email": activate_account.email}, format="json"
    )

    assert expected_status_code == actual_response.status_code
    assert expected_detail_message == actual_response.data["detail"]
    assert expected_code == actual_response.data["code"]
