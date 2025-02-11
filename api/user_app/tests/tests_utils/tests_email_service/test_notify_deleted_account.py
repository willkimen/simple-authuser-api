import pytest
from user_app.utils.email_service import notify_deleted_account

# ========== Objects and constants ============
EMAIL = "fakeemail@email.com"


# =============== Tests ================
@pytest.mark.django_db
def test_success_send_email():
    """
    The purpose of this test is to ensure that the function is working correctly and
    that it returns the expected number of emails sent.

    **Expected Results**:
    - The test passes if the function returns the correct number of emails sent
      (1). If the returned number is different, the test fails, indicating that
      there was an issue with sending the email.
    """
    expected_send_count = 1
    actual_sent_count = notify_deleted_account(EMAIL)
    assert expected_send_count == actual_sent_count
