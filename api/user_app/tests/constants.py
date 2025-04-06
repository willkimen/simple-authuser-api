import importlib

from django.contrib.auth import get_user_model

# Gets the user model configured in the Django project.
# Used for reference in tests where the user model is needed.
User = get_user_model()

# =====================================
# CONSTANTS FOR FAKE DATA
# =====================================

# Fake values used as examples in tests.
FAKE_SECRET = "fake_secret"
FAKE_CODE = "fake_code"

# =====================================
# CONSTANTS FOR PATCHING IMPORTS
# =====================================

# Path to the `TOKEN_SECRET` variable in a module being tested.
# This constant is used to patch the variable import within
# the context of the tested module.
TOKEN_SECRET_SETTING_TO_PATCH = "settings.TOKEN_SECRET"

# =====================================
# CONSTANTS FOR PATCHING FUNCTIONS AND CLASSES
# =====================================
# Paths to functions and classes that will be mocked in tests.


# Constant for mocking message logging
LOGGER_EMAIL_TASK_ERROR_FUNCTION_PATCH = "logger.email_task_error"

# Constant for mocking the method that limits the number of requests
ALLOW_REQUEST_FUNCTION_TO_PATCH = "FivePerMinuteRateLimit.allow_request"

# Constants for mocking functions that send confirmation codes to users
SEND_EMAIL_CHANGE_CODE_FUNCTION_TO_PATCH = "send_email_change_code"
SEND_RESET_PASSWORD_CODE_FUNCTION_TO_PATCH = "send_reset_password_code"
SEND_ACCOUNT_ACTIVATION_CODE_FUNCTION_TO_PATCH = "send_account_activation_code"

# Constants for mocking functions that notify the user
NOTIFY_ACTIVATED_ACCOUNT_FUNCTION_TO_PATCH = "notify_activated_account"
NOTIFY_CHANGED_EMAIL_FUNCTION_TO_PATCH = "notify_changed_email"
NOTIFY_RESET_PASSWORD_FUNCTION_TO_PATCH = "notify_reset_password"
NOTIFY_DELETED_ACCOUNT_FUNCTION_TO_PATCH = "notify_deleted_account"
NOTIFY_FIRST_REMINDER_FUNCTION_TO_PATCH = "notify_first_reminder"
NOTIFY_SECOND_REMINDER_FUNCTION_TO_PATCH = "notify_second_reminder"
NOTIFY_EXPIRED_ACCOUNT_DELETION_FUNCTION_TO_PATCH = "notify_expired_account_deletion"

# Constant for mocking the utility function that generates a random code
GENERATE_RANDOM_CODE_FUNCTION_TO_PATCH = "generate_random_code"

# Constant for mocking the class responsible for sending emails
EMAIL_MULTI_CLASS_TO_PATCH = "EmailMultiAlternatives"

# Constants for mocking functions related to tokens
REVOKE_TOKENS_FUNCTION_TO_PATCH = "revoke_tokens"
CREATE_PAYLOAD_FUNCTION_TO_PATCH = "create_payload"
CREATE_PAIR_TOKEN_FUNCTION_TO_PATCH = "create_pair_token"

# Constants for mocking email notification classes
ACTIVATION_NOTIFICATION_EMAIL_CLASS_TO_PATCH = "ActivationNotificationEmail"
CHANGE_NOTIFICATION_EMAIL_CLASS_TO_PATCH = "ChangeNotificationEmail"
PASSWORD_RESET_NOTIFICATION_EMAIL_CLASS_TO_PATCH = "PasswordResetNotificationEmail"
DELETED_ACCOUNT_NOTIFICATION_EMAIL_CLASS_TO_PATCH = "DeletedAccountNotificationEmail"
DEACTIVATED_ACCOUNT_NOTIFICATION_EMAIL_CLASS_TO_PATCH = (
    "DeactivatedAccountNotificationEmail"
)
EXPIRED_ACCOUNT_DELETION_EMAIL_CLASS_TO_PATCH = "ExpiredAccountDeletionEmail"

# Method related to the notification email classes above
SEND_WITH_ERROR_HANDLING_METHOD_TO_PATCH = "send_with_error_handling"

# Constants for mocking classes that manage confirmation codes
CHANGE_CODE_EMAIL_CLASS_TO_PATCH = "ChangeCodeEmail"
ACTIVATION_CODE_EMAIL_CLASS_TO_PATCH = "ActivationCodeEmail"
RESET_PASSWORD_CODE_EMAIL_CLASS_TO_PATCH = "ResetPasswordCodeEmail"


# =====================================
# CONSTANTS FOR PATCHING MODULES
# =====================================

# Dynamic paths for specific modules used in the system.
# They use `importlib.import_module` to load the module names.

# Path to the token-related utility module.
TOKEN_UTILS_MODULE_PATH = importlib.import_module(
    "user_app.authentication.token_service"
).__name__

# Path to the view responsible for user account activation.
ACTIVATE_ACCOUNT_VIEWS_MODULE_PATH = importlib.import_module(
    "user_app.views.activate_account_views"
).__name__

# Path to the view responsible for password reset.
RESET_PASSWORD_VIEWS_MODULE_PATH = importlib.import_module(
    "user_app.views.reset_password_views"
).__name__

# Path to the CRUD module used in views.
CRUD_VIEWS_MODULE_PATH = importlib.import_module("user_app.views.crud_views").__name__

# Path to the view responsible for email change.
CHANGE_EMAIL_VIEWS_MODULE_PATH = importlib.import_module(
    "user_app.views.change_email_views"
).__name__

# Path to the email service module, containing email sending functions.
EMAIL_SERVICE_MODULE_PATH = importlib.import_module(
    "user_app.email.email_service"
).__name__

# Path to the tasks module, containing celery tasks functions.
TASKS_MODULE_PATH = importlib.import_module("user_app.tasks").__name__
