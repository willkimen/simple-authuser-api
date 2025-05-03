"""
This module provides detailed messages and code for http responses.
"""

VALIDATION_ERRORS = {
    "code": "VALIDATION_ERRORS",
    "detail": "Some fields are invalid. Please review and try again.",
}

ERROR_SENDING_EMAIL = {
    "code": "ERROR_SENDING_EMAIL",
    "detail": "There was an error sending the email. Please try again later.",
}

ACCOUNT_REGISTERED_SUCCESSFULLY = {
    "code": "ACCOUNT_REGISTERED_SUCCESSFULLY",
    "detail": "Registration successful! A confirmation email has been sent.",
}

ACCOUNT_NOT_FOUND = {
    "code": "ACCOUNT_NOT_FOUND",
    "detail": "Account not found. Please check the information and try again.",
}

EMAIL_ALREADY_EXISTS = {
    "code": "EMAIL_ALREADY_EXISTS",
    "detail": "An account with this email already exists.",
}

EMAIL_ALREADY_IN_USE = {
    "code": "EMAIL_ALREADY_IN_USE",
    "detail": "This email is already associated with your account.",
}

ACCOUNT_UPDATED_SUCCESSFULLY = {
    "code": "ACCOUNT_UPDATED_SUCCESSFULLY",
    "detail": "Your information was updated successfully.",
}

ACCOUNT_DELETED_SUCCESSFULLY = {
    "code": "ACCOUNT_DELETED_SUCCESSFULLY",
    "detail": "Account deleted successfully.",
}

CODE_NOT_FOUND = {
    "code": "CODE_NOT_FOUND",
    "detail": "The code provided was not found. Please check and try again.",
}

ACCOUNT_HAS_ALREADY_ACTIVATED = {
    "code": "ACCOUNT_HAS_ALREADY_ACTIVATED",
    "detail": "Your account has already been activated.",
}

CODE_EXPIRED = {
    "code": "CODE_EXPIRED",
    "detail": "The code has expired. Please request a new verification code.",
}

ACCOUNT_EMAIL_CHANGED = {
    "code": "ACCOUNT_EMAIL_CHANGED",
    "detail": "Email changed successfully. Please log in again using your new email address.",
}

ACCOUNT_PASSWORD_CHANGED = {
    "code": "ACCOUNT_PASSWORD_CHANGED",
    "detail": "Password changed successfully. Please log in again using your new password.",
}

ACCOUNT_PASSWORD_RESET = {
    "code": "ACCOUNT_PASSWORD_RESET",
    "detail": "Password reset successfully. Please log in again using your new password.",
}

PASSWORD_INCORRECT = {
    "code": "PASSWORD_INCORRECT",
    "detail": "The current password is incorrect. Please try again.",
}

ACTIVATED_ACCOUNT = {
    "code": "ACCOUNT_ACTIVATED",
    "detail": "Your account was successfully activated.",
}

EMAIL_SEND_TO_ACCOUNT_SUCCESSFULLY = {
    "code": "EMAIL_SEND_TO_ACCOUNT_SUCCESSFULLY",
    "detail": "Email sent successfully.",
}

ACCOUNT_NOT_ACTIVATED = {
    "code": "ACCOUNT_NOT_ACTIVATED",
    "detail": "Your account has not been activated yet.",
}

LOGOUT_SUCCESSFUL = {
    "code": "LOGOUT_SUCCESSFUL",
    "detail": "Logout successful. Session ended.",
}

LOGIN_SUCCESSFUL = {
    "code": "LOGIN_SUCCESSFUL",
    "detail": "Login successful. Access granted.",
}

TOKEN_ACCESS_CREATED = {
    "code": "TOKEN_ACCESS_CREATED",
    "detail": "Access token created successfully.",
}

IS_NOT_REFRESH_TOKEN = {
    "code": "IS_NOT_REFRESH_TOKEN",
    "detail": "The token provided is not a refresh token.",
}

IS_NOT_ACCESS_TOKEN = {
    "code": "IS_NOT_ACCESS_TOKEN",
    "detail": "The token provided is not an access token.",
}

IS_NOT_ACCESS_OR_REFRESH_TOKEN = {
    "code": "IS_NOT_ACCESS_OR_REFRESH_TOKEN",
    "detail": "The token provided is neither an access nor a refresh token.",
}

ACCOUNT_TOKEN_MISMATCH = {
    "code": "ACCOUNT_TOKEN_MISMATCH",
    "detail": "The authenticated account does not match the account associated with the token.",
}


TOKEN_IS_VALID = {
    "code": "TOKEN_IS_VALID",
    "detail": "The provided token is valid and can be used for authentication.",
}
