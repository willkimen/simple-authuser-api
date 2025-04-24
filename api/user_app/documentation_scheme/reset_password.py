from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiResponse
from user_app.constants.response_codes_and_messages import (
    CODE_EXPIRED,
    CODE_NOT_FOUND,
    EMAIL_SEND_TO_USER_SUCCESSFULLY,
    USER_ACCOUNT_NOT_ACTIVATED,
    USER_NOT_FOUND,
    USER_PASSWORD_RESET,
    VALIDATION_ERRORS,
)
from user_app.constants.validation_error_messages import (
    BLANK_FIELD,
    COMMON_PASSWORD,
    INVALID_FORMAT_EMAIL,
    NULL_FIELD,
    NUMERIC_PASSWORD,
    PASSWORD_DO_NOT_MATCH,
    REQUIRED_FIELD,
    SHORT_PASSWORD,
)

email_send_to_user_response = {
    "type": "object",
    "example": EMAIL_SEND_TO_USER_SUCCESSFULLY,
}

email_validation_errors_response = {
    "type": "object",
    "example": {
        **VALIDATION_ERRORS,
        "field_errors": {
            "email": [
                INVALID_FORMAT_EMAIL,
                REQUIRED_FIELD,
                NULL_FIELD,
                BLANK_FIELD,
            ],
        },
    },
}

user_not_found_response = {
    "type": "object",
    "example": USER_NOT_FOUND,
}

user_account_not_activated_response = {
    "type": "object",
    "example": USER_ACCOUNT_NOT_ACTIVATED,
}

user_password_reset_response = {
    "type": "object",
    "example": {
        **USER_PASSWORD_RESET,
        "access": "string jwt",
        "refresh": "string jwt",
    },
}

code_not_found_response = {
    "type": "object",
    "example": CODE_NOT_FOUND,
}

code_expired_response = {
    "type": "object",
    "example": CODE_EXPIRED,
}


passwords_validation_errors_response = OpenApiResponse(
    response=OpenApiTypes.OBJECT,
    description="Passwords Validation Errors",
    examples=[
        OpenApiExample(
            "Password Validation Errors",
            value={
                **VALIDATION_ERRORS,
                "field_errors": {
                    "password": [
                        SHORT_PASSWORD,
                        COMMON_PASSWORD,
                        NUMERIC_PASSWORD,
                        REQUIRED_FIELD,
                        NULL_FIELD,
                        BLANK_FIELD,
                    ],
                },
            },
        ),
        OpenApiExample(
            "Confirmation Password Validation Error",
            value={
                **VALIDATION_ERRORS,
                "field_errors": {
                    "confirmation_password": PASSWORD_DO_NOT_MATCH,
                },
            },
        ),
    ],
)
