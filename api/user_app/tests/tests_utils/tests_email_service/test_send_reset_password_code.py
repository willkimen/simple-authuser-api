import pytest
from user_app.models import ResetPasswordCodeModel
from user_app.utils.email_service import send_reset_password_code


# =============== Tests ================
@pytest.mark.django_db
def test_success_send_email(deactivated_user):
    """
    The purpose of this test is to ensure that the function is working correctly and
    that it returns the expected number of emails sent.

    **Expected Results**:
    - The test passes if the function returns the correct number of emails sent
      (1). If the returned number is different, the test fails, indicating that
      there was an issue with sending the email.
    """
    expected_send_count = 1
    actual_sent_count = send_reset_password_code(deactivated_user.email)
    assert expected_send_count == actual_sent_count


@pytest.mark.django_db
def test_success_send_email_create_code_in_database(deactivated_user):
    """
    Tests if the password reset code is successfully sent via email
    and if the code is created in the database.

    Verifies that the email sending function is called and that the
    password reset code has been stored in the ResetPasswordCodeModel table.
    """
    send_reset_password_code(deactivated_user.email)

    assert ResetPasswordCodeModel.objects.filter(
        user_id=deactivated_user.email
    ).exists()
    assert (
        ResetPasswordCodeModel.objects.filter(user_id=deactivated_user.email).count()
        == 1
    )
