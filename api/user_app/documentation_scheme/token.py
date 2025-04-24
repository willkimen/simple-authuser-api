from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiResponse
from user_app.constants.response_codes_and_messages import (
    IS_NOT_ACCESS_OR_REFRESH_TOKEN,
    IS_NOT_REFRESH_TOKEN,
    LOGIN_SUCCESSFUL,
    LOGOUT_SUCCESSFUL,
    TOKEN_ACCESS_CREATED,
    TOKEN_IS_VALID,
    USER_ACCOUNT_NOT_ACTIVATED,
    USER_NOT_FOUND,
    USER_TOKEN_MISMATCH,
)
from user_app.constants.token_exception_messages import (
    DECODE_ERROR,
    EXPIRED_SIGNATURE,
    INVALID_ALGORITHM,
    INVALID_SIGNATURE,
    INVALID_TOKEN,
    TOKEN_IN_BLACKLIST,
)

obtain_token_pair_request = {
    "application/json": {
        "type": "object",
        "example": {"email": "user@example.com", "password": "string"},
    }
}

user_not_found_response = {
    "type": "object",
    "example": USER_NOT_FOUND,
}

user_account_not_activated_response = {
    "type": "object",
    "example": USER_ACCOUNT_NOT_ACTIVATED,
}

login_successful_response = {
    "type": "object",
    "example": {
        **LOGIN_SUCCESSFUL,
        "access": "string jwt",
        "refresh": "string jwt",
    },
}

refresh_request = {
    "application/json": {
        "type": "object",
        "example": {"refresh": "string refresh token"},
    }
}

blacklist_token_and_user_not_activated = OpenApiResponse(
    response=OpenApiTypes.OBJECT,
    description="Token In Blacklist or User Account Not Activated",
    examples=[
        OpenApiExample("Token In Blacklist", value=TOKEN_IN_BLACKLIST),
        OpenApiExample("User Account Not Activated", value=USER_ACCOUNT_NOT_ACTIVATED),
    ],
)

authentication_errors_response = OpenApiResponse(
    response=OpenApiTypes.OBJECT,
    description="Token Authentication Errors",
    examples=[
        OpenApiExample("Token decode error", value=DECODE_ERROR),
        OpenApiExample("Invalid token", value=INVALID_TOKEN),
        OpenApiExample("Invalid signature", value=INVALID_SIGNATURE),
        OpenApiExample("Expired signature", value=EXPIRED_SIGNATURE),
        OpenApiExample("Invalid algorithm", value=INVALID_ALGORITHM),
    ],
)

token_access_created_response = {
    "type": "object",
    "example": {
        **TOKEN_ACCESS_CREATED,
        "access": "string jwt",
    },
}

is_not_refresh_response = {
    "type": "object",
    "example": IS_NOT_REFRESH_TOKEN,
}


blacklist_token_and_user_token_mismatch = OpenApiResponse(
    response=OpenApiTypes.OBJECT,
    description="Token In Blacklist or User Token Mismatch",
    examples=[
        OpenApiExample("Token In Blacklist", value=TOKEN_IN_BLACKLIST),
        OpenApiExample("User Token Mismatch", value=USER_TOKEN_MISMATCH),
    ],
)


blacklist_request = {
    "application/json": {
        "type": "object",
        "example": {"token": "string access_or_refresh_token"},
    }
}

logout_successful_response = {
    "type": "object",
    "example": LOGOUT_SUCCESSFUL,
}

is_not_access_or_refresh_response = {
    "type": "object",
    "example": IS_NOT_ACCESS_OR_REFRESH_TOKEN,
}

verify_token_request = {
    "application/json": {
        "type": "object",
        "example": {"token": "string access_or_refresh_token"},
    }
}

blacklist_response = {
    "type": "object",
    "example": TOKEN_IN_BLACKLIST,
}


token_is_valid_response = {
    "type": "object",
    "example": TOKEN_IS_VALID,
}
