from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Custom exception handler to add error codes and modify error messages in API responses.

    Args:
        exc (Exception): The exception that was raised.
        context (dict): Additional context about the request.

    Returns:
        Response: The modified response object with added error code and message.

    This function extends the default exception handler provided by Django REST framework.
    It adds an "error_code" field to the response data and renames the "detail" field to "message".
    """
    # Call the default exception handler to get the standard error response
    response = exception_handler(exc, context)

    # If a response is returned, modify it
    if response is not None:
        # Add the error code to the response data
        response.data["error_code"] = exc.default_code
        # Rename the "detail" field to "message"
        response.data["message"] = response.data.pop("detail")

    return response
