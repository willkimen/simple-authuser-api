"""
Module for verification code prefixes.

This module centralizes the prefixes used in verification codes to differentiate 
between different types of actions, such as email change, account activation, 
and password reset. These prefixes are used not only by the verification code classes 
but also by other functions that require consistency in code identification.

Constants:
    CHANGE_EMAIL_PREFIX (str): Prefix for email change verification codes.
    ACTIVATE_ACCOUNT_PREFIX (str): Prefix for account activation verification codes.
    RESET_PASSWORD_PREFIX (str): Prefix for password reset verification codes.
"""

CHANGE_EMAIL_PREFIX = "chgmail"
ACTIVATE_ACCOUNT_PREFIX = "actacc"
RESET_PASSWORD_PREFIX = "rstpwd"
