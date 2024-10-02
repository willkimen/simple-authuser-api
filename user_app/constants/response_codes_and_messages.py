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

USER_REGISTERED_SUCCESSFULLY = {
    "code": "USER_REGISTERED_SUCCESSFULLY",
    "detail": "Registration successful! A confirmation email has been sent.",
}

USER_NOT_FOUND = {
    "code": "USER_NOT_FOUND",
    "detail": "User not found. Please check the information and try again.",
}

EMAIL_ALREADY_EXISTS = {
    "code": "EMAIL_ALREADY_EXISTS",
    "detail": "An account with this email already exists.",
}

EMAIL_ALREADY_IN_USE = {
    "code": "EMAIL_ALREADY_IN_USE",
    "detail": "This email is already associated with your account.",
}

USER_UPDATED_SUCCESSFULLY = {
    "code": "USER_UPDATED_SUCCESSFULLY",
    "detail": "Your information was updated successfully.",
}

USER_DELETED_SUCCESSFULLY = {
    "code": "USER_DELETED_SUCCESSFULLY",
    "detail": "Account deleted successfully.",
}

CODE_NOT_FOUND = {
    "code": "CODE_NOT_FOUND",
    "detail": "The code provided was not found. Please check and try again.",
}

USER_HAS_ALREADY_ACTIVATED = {
    "code": "USER_HAS_ALREADY_ACTIVATED",
    "detail": "Your account has already been activated.",
}

CODE_EXPIRED = {
    "code": "CODE_EXPIRED",
    "detail": "The code has expired. Please request a new activation code.",
}

USER_EMAIL_CHANGED = {
    "code": "USER_EMAIL_CHANGED",
    "detail": "Email changed successfully. Please log in again using your new email address.",
}

USER_PASSWORD_CHANGED = {
    "code": "USER_PASSWORD_CHANGED",
    "detail": "Password changed successfully. Please log in again using your new password.",
}

USER_PASSWORD_RESET = {
    "code": "USER_PASSWORD_RESET",
    "detail": "Password reset successfully. Please log in again using your new password.",
}

PASSWORD_DO_NOT_MATCH = {
    "code": "PASSWORD_DO_NOT_MATCH",
    "detail": "The current password is incorrect. Please try again.",
}

ACTIVATED_USER = {
    "code": "USER_ACTIVATED",
    "detail": "Your account was successfully activated.",
}

EMAIL_SEND_TO_USER_SUCCESSFULLY = {
    "code": "EMAIL_SEND_TO_USER_SUCCESSFULLY",
    "detail": "Email sent successfully.",
}

USER_ACCOUNT_NOT_ACTIVATED = {
    "code": "USER_ACCOUNT_NOT_ACTIVATED",
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

USER_TOKEN_MISMATCH = {
    "code": "USER_TOKEN_MISMATCH",
    "detail": "The authenticated user does not match the user associated with the token.",
}
