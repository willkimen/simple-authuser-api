from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc: Exception, context: dict) -> Response | None:
    """
    Custom exception handler to add error codes and modify error messages
    in API responses.

    Args:
        exc (Exception): The exception that was raised.
        context (dict): Additional context about the request.

    Returns:
        Response: The modified response object with added error code.
    """
    # Call the default exception handler to get the standard error response
    response: Response | None = exception_handler(exc, context)

    # If a response is returned, modify it
    if response is not None:
        # Add the error code to the response data
        response.data["code"] = exc.default_code

    return response
