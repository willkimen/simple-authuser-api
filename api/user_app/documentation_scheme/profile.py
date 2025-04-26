from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiResponse
from user_app.constants.http_response import (
    PASSWORD_INCORRECT,
    USER_DELETED_SUCCESSFULLY,
    USER_PASSWORD_CHANGED,
    USER_REGISTERED_SUCCESSFULLY,
    USER_UPDATED_SUCCESSFULLY,
    VALIDATION_ERRORS,
)
from user_app.constants.validation_error_messages import (
    BLANK_FIELD,
    COMMON_PASSWORD,
    EMAIL_ALREADY_EXISTS,
    INVALID_FORMAT_EMAIL,
    LONG_FIELD,
    NULL_FIELD,
    NUMERIC_PASSWORD,
    PASSWORD_DO_NOT_MATCH,
    REQUIRED_FIELD,
    SHORT_PASSWORD,
)

data_user_deactivated = {
    "id": 1,
    "first_name": "string",
    "last_name": "string",
    "email": "user@example.com",
    "is_active": False,
}

data_user_activated = {
    "id": 1,
    "first_name": "string",
    "last_name": "string",
    "email": "user@example.com",
    "is_active": True,
}


register_validation_errors_response = OpenApiResponse(
    response=OpenApiTypes.OBJECT,
    description="Multiple Validation Errors",
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
        OpenApiExample(
            "Email Validation Errors",
            value={
                **VALIDATION_ERRORS,
                "field_errors": {
                    "email": [
                        INVALID_FORMAT_EMAIL,
                        EMAIL_ALREADY_EXISTS,
                        REQUIRED_FIELD,
                        NULL_FIELD,
                        BLANK_FIELD,
                    ],
                },
            },
        ),
        OpenApiExample(
            "First Name Validation Errors",
            value={
                **VALIDATION_ERRORS,
                "field_errors": {
                    "first_name": [
                        LONG_FIELD,
                        REQUIRED_FIELD,
                        NULL_FIELD,
                        BLANK_FIELD,
                    ],
                },
            },
        ),
        OpenApiExample(
            "Last Name Validation Errors",
            value={
                **VALIDATION_ERRORS,
                "field_errors": {
                    "last_name": [
                        LONG_FIELD,
                        REQUIRED_FIELD,
                        NULL_FIELD,
                        BLANK_FIELD,
                    ],
                },
            },
        ),
    ],
)

update_validation_errors_response = OpenApiResponse(
    response=OpenApiTypes.OBJECT,
    description="Multiple Validation Errors",
    examples=[
        OpenApiExample(
            "First Name Validation Errors",
            value={
                **VALIDATION_ERRORS,
                "field_errors": {
                    "first_name": [
                        LONG_FIELD,
                        REQUIRED_FIELD,
                        NULL_FIELD,
                        BLANK_FIELD,
                    ],
                },
            },
        ),
        OpenApiExample(
            "Last Name Validation Errors",
            value={
                **VALIDATION_ERRORS,
                "field_errors": {
                    "last_name": [
                        LONG_FIELD,
                        REQUIRED_FIELD,
                        NULL_FIELD,
                        BLANK_FIELD,
                    ],
                },
            },
        ),
    ],
)


user_registered_response = {
    "type": "object",
    "example": {
        **USER_REGISTERED_SUCCESSFULLY,
        "user": data_user_deactivated,
    },
}

user_updated_response = {
    "type": "object",
    "example": {
        **USER_UPDATED_SUCCESSFULLY,
        "user": data_user_activated,
    },
}

user_detail_response = {
    "type": "object",
    "example": {
        "user": data_user_activated,
    },
}

user_deleted_response = {
    "type": "object",
    "example": USER_DELETED_SUCCESSFULLY,
}

user_password_changed_response = {
    "type": "object",
    "example": {
        **USER_PASSWORD_CHANGED,
        "access": "string jwt",
        "refresh": "string jwt",
    },
}

password_validation_errors_and_incorrect_password_response = OpenApiResponse(
    response=OpenApiTypes.OBJECT,
    description="Validation Password Errors or Incorrect Password",
    examples=[
        OpenApiExample(
            name="Incorrect Password",
            value=PASSWORD_INCORRECT,
        ),
        OpenApiExample(
            name="Validation Password Errors",
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
    ],
)
