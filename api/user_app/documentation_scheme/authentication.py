from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiResponse
from user_app.constants.authentication_error_messages import (
    AUTHORIZATION_HEADER_MISSING,
    AUTHORIZATION_HEADER_WITHOUT_BEARER,
    INVALID_AUTHORIZATION_HEADER_FORMAT,
)
from user_app.constants.token_exception_messages import (
    DECODE_ERROR,
    EXPIRED_SIGNATURE,
    INVALID_ALGORITHM,
    INVALID_SIGNATURE,
    INVALID_TOKEN,
    TOKEN_IN_BLACKLIST,
)

authentication_errors_response = OpenApiResponse(
    response=OpenApiTypes.OBJECT,
    description="Authentication Errors",
    examples=[
        OpenApiExample(
            "Authorization Header Missing",
            value={
                "code": "authentication_failed",
                "detail": AUTHORIZATION_HEADER_MISSING,
            },
        ),
        OpenApiExample(
            "Invalid Authorization Header Format",
            value={
                "code": "authentication_failed",
                "detail": INVALID_AUTHORIZATION_HEADER_FORMAT,
            },
        ),
        OpenApiExample(
            "Authorization Header Without 'Bearer'",
            value={
                "code": "authentication_failed",
                "detail": AUTHORIZATION_HEADER_WITHOUT_BEARER,
            },
        ),
        OpenApiExample("Token Decode Error", value=DECODE_ERROR),
        OpenApiExample("Invalid Token", value=INVALID_TOKEN),
        OpenApiExample("Invalid Signature", value=INVALID_SIGNATURE),
        OpenApiExample("Expired Signature", value=EXPIRED_SIGNATURE),
        OpenApiExample("Invalid Algorithm", value=INVALID_ALGORITHM),
        OpenApiExample("Token In Blacklist", value=TOKEN_IN_BLACKLIST),
    ],
)
