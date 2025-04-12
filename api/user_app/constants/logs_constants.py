# =====================================
# Constants related to email_task_error logging
# =====================================
EMAIL_TASK_ERROR_LEVEL = 35
EMAIL_TASK_ERROR_LEVEL_NAME = "EMAIL_TASK_ERROR"
EMAIL_TASK_ERROR_LOGGER_NAME = "email_task_error"

email_task_error_message_format = "tag={tag};to={to};error={error}"
FAILED_SEND_ACCOUNT_ACTIVATION_CODE_TAG = "send_account_activation_code_failed"
FAILED_SEND_EMAIL_CHANGE_CODE_TAG = "send_email_change_code_failed"
FAILED_SEND_RESET_PASSWORD_CODE_TAG = "send_password_reset_code_failed"
FAILED_NOTIFY_ACTIVATED_ACCOUNT_TAG = "account_activation_notification_failed"
FAILED_NOTIFY_CHANGED_EMAIL_TAG = "email_change_notification_failed"
FAILED_NOTIFY_RESET_PASSWORD_TAG = "password_reset_notification_failed"
FAILED_NOTIFY_DELETED_ACCOUNT_TAG = "account_deletion_notification_failed"
FAILED_NOTIFY_FIRST_REMINDER_TAG = "first_reminder_failed"
FAILED_NOTIFY_SECOND_REMINDER_TAG = "second_reminder_failed"
FAILED_NOTIFY_EXPIRED_ACCOUNT_DELETION_TAG = (
    "expired_account_deletion_notification_failed"
)
