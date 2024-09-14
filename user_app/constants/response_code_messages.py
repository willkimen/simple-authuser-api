"""
This module provides detailed messages and code for http responses.
"""

VALIDATION_ERRORS = {
    "code": "VALIDATION_ERRORS",
    "detail": "There are field validation errors.",
}

ERROR_SENDING_EMAIL = {
    "code": "ERROR_SENDING_EMAIL",
    "detail": "A server error occurred when sending email to the user.",
}

USER_REGISTERED_SUCCESSFULLY = {
    "code": "USER_REGISTERED_SUCCESSFULLY",
    "detail": "An email with the account confirmation code has been sent to the user's email address.",
}

USER_NOT_FOUND = {
    "code": "USER_NOT_FOUND",
    "detail": "User not found in our database. Please check user data.",
}

EMAIL_ALREADY_EXISTS = {
    "code": "EMAIL_ALREADY_EXISTS",
    "detail": "A user with this email address already exists.",
}

EMAIL_ALREADY_IN_USE = {
    "code": "EMAIL_ALREADY_IN_USE",
    "detail": "This is already your current email address.",
}

USER_UPDATED_SUCCESSFULLY = {
    "code": "USER_UPDATED_SUCCESSFULLY",
    "detail": "User updated successfully.",
}

USER_DELETED_SUCCESSFULLY = {
    "code": "USER_DELETED_SUCCESSFULLY",
    "detail": "User deleted successfully.",
}

CODE_NOT_FOUND = {
    "code": "CODE_NOT_FOUND",
    "detail": "The code received was not found.",
}

USER_HAS_ALREADY_ACTIVATED = {
    "code": "USER_HAS_ALREADY_ACTIVATED",
    "detail": "User has already confirmed email and is activated.",
}

CODE_EXPIRED = {
    "code": "CODE_EXPIRED",
    "detail": "The code has expired.",
}

USER_EMAIL_CHANGED = {
    "code": "USER_EMAIL_CHANGED",
    "detail": "User email was changed successfully.",
}

USER_ACTIVATED = {
    "code": "USER_ACTIVATED",
    "detail": "User account successfully activated.",
}

CODE_FIELD_IS_REQUIRED = {
    "code": "CODE_FIELD_IS_REQUIRED",
    "detail": "The 'code' field is required.",
}

EMAIL_SEND_TO_USER_SUCCESSFULLY = {
    "code": "EMAIL_SEND_TO_USER_SUCCESSFULLY",
    "detail": "Email sent to user successfully.",
}

USER_ACCOUNT_NOT_ACTIVATED = {
    "code": "USER_ACCOUNT_NOT_ACTIVATED",
    "detail": "User does not have the account activated.",
}

LOGOUT_SUCCESSFUL = {
    "code": "LOGOUT_SUCCESSFUL",
    "detail": "User was successfully logged out and token was made invalid.",
}


LOGIN_SUCCESSFUL = {
    "code": "LOGIN_SUCCESSFUL",
    "detail": "User was successfully logged in. An access and refresh was returned.",
}

TOKEN_ACCESS_CREATED = {
    "code": "TOKEN_ACCESS_CREATED",
    "detail": "Access token was created successfully.",
}

IS_NOT_REFRESH_TOKEN = {
    "code": "IS_NOT_REFRESH_TOKEN",
    "detail": "The token sent is not a refresh type.",
}

IS_NOT_ACCESS_TOKEN = {
    "code": "IS_NOT_ACCESS_TOKEN",
    "detail": "The token sent is not a access type.",
}

IS_NOT_ACCESS_OR_REFRESH_TOKEN = {
    "code": "IS_NOT_ACCESS_OR_REFRESH_TOKEN",
    "detail": "The token sent is not a access or refresh type.",
}

USER_TOKEN_MISMATCH = {
    "code": "USER_TOKEN_MISMATCH",
    "detail": "The logged-in user is different from the user associated with the token.",
}
