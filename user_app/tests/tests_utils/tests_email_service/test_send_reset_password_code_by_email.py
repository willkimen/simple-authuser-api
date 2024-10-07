from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model

from user_app.constants.path_for_mock import email_service_module_path
from user_app.models import ResetPasswordCodeModel
from user_app.utils.email_service import send_reset_password_code_by_email

# ========== Objects and constants ============
User = get_user_model()
CODE = "mocked_code"
email_multi_class = "EmailMultiAlternatives"
generate_random_code = "generate_random_code"


# =============== Fixtures ================
@pytest.fixture
def deactivated_user():
    """
    Fixture to create and return a deactivated User object.
    """
    return User.objects.create_user(
        first_name="fake_first_name",
        last_name="fake_last_name",
        email="fakeemail@email.com",
        password="FAKEpassword10!",
    )


# =============== Tests ================
@pytest.mark.django_db
@patch(f"{email_service_module_path}.{email_multi_class}")
def test_success_send_email(MockEmailMultiAlternatives: MagicMock, deactivated_user):
    # Returns a mocked instance of the EmailMultiAlternatives class
    mock_email_multi_instance = MockEmailMultiAlternatives.return_value

    send_reset_password_code_by_email(deactivated_user.email)

    mock_email_multi_instance.send.assert_called()


@pytest.mark.django_db
@patch(f"{email_service_module_path}.{email_multi_class}")
@patch(f"{email_service_module_path}.{generate_random_code}", return_value=CODE)
def test_success_send_email_create_code_in_database(
    mock_generate_random_code: MagicMock,
    MockEmailMultiAlternatives: MagicMock,
    deactivated_user,
):
    # Returns a mocked instance of the EmailMultiAlternatives class
    mock_email_multi_instance = MockEmailMultiAlternatives.return_value

    send_reset_password_code_by_email(deactivated_user.email)

    mock_email_multi_instance.send.assert_called()

    assert ResetPasswordCodeModel.objects.filter(code=CODE).exists()
