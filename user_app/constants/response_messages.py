"""
This module contains constants for response messages used in views or other parts
of the code that need to provide HTTP responses.
"""

# Message displayed when there is an error trying to send an email.
ERROR_SENDING_EMAIL = "Error sending email."

# Message displayed when a user is successfully registered.
USER_REGISTERED_SUCCESSFULLY = "User registered successfully."

# Message displayed when a user is not found in the system.
USER_NOT_FOUND = "User not found."

# Message displayed when a user's information is successfully updated.
USER_UPDATED_SUCCESSFULLY = "User updated successfully."

# Message displayed when the account activation code is not found.
ACCOUNT_ACTIVATION_CODE_NOT_FOUND = "Account activation code not found."

# Message displayed when the user has already confirmed their email and activated their account.
USER_HAS_ALREADY_ACTIVATED = "User has already confirmed email and is activated."

# Message displayed when the confirmation code type is invalid.
INVALID_CONFIRMATION_CODE_TYPE = "Invalid confirmation code type."

# Message displayed when the confirmation code has expired.
CODE_EXPIRED = "Code expired."

# Message displayed when the user's account is successfully activated.
ACCOUNT_ACTIVATED = "User account successfully activated."

# Message displayed when the 'code' field is required but not provided.
CODE_FIELD_IS_REQUIRED = "The 'code' field is required."

# Message displayed when the email is successfully sent to the user.
EMAIL_SEND_TO_USER_SUCCESSFULLY = "Email sent to user successfully."

# Message displayed when the user does not have their account activated.
USER_ACCOUNT_NOT_ACTIVATED = "User does not have the account activated."
