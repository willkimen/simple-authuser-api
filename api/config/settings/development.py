import os

from .base import *

# Debugging mode on for development
# -----------------------------------------------------------------------------
DEBUG = True


# Security
# -----------------------------------------------------------------------------
SECRET_KEY = os.environ.get("SECRET_KEY", "secret_insecure_jldsfj5165ser5wg16ae5344*")

ALLOWED_HOSTS: list[str] = [
    host.strip() for host in os.environ.get("ALLOWED_HOSTS", "").split(",")
]

CORS_ALLOWED_ORIGINS: list[str] = [
    origin.strip() for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
]

TOKEN_SECRET = os.environ.get(
    "TOKEN_SECRET", "secret_token_insecure_jldsfj51dfsd65fsklj564564wg16ae5344*"
)


# URL configurations
# -----------------------------------------------------------------------------
RESET_PASSWORD_LINK = os.environ.get("REDIRECT_TO_RESET_PASSWORD_PAGE", "")
ACTIVATE_ACCOUNT_LINK = os.environ.get("REDIRECT_TO_ACTIVATE_ACCOUNT_PAGE", "")
LOGIN_LINK = os.environ.get("REDIRECT_TO_LOGIN_PAGE", "")
REGISTER_LINK = os.environ.get("REDIRECT_TO_REGISTER_PAGE", "")
REQUEST_NEW_ACTIVATE_ACCOUNT_CODE_LINK = os.environ.get(
    "REDIRECT_TO_REQUEST_NEW_ACTIVATE_ACCOUNT_CODE_PAGE", ""
)


# Database (Use if you want postgres with docker container.)
# -----------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB"),
        "USER": os.environ.get("POSTGRES_USER"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        "HOST": os.environ.get("POSTGRES_HOST"),
        "PORT": os.environ.get("POSTGRES_PORT"),
    }
}

"""
# Database (User if you want it locally on your host machine.)
# -----------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
"""


# Email settings for development
# -----------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


"""
OBS.: In case you want to use a real email service.
# Email settings
# -----------------------------------------------------------------------------
# Define the email backend to be used by Django. In this case, the SMTP backend.
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# Get the SMTP server host from environment variables.
EMAIL_HOST = os.environ.get("EMAIL_HOST")

# Get the SMTP server port from environment variables.
EMAIL_PORT = os.environ.get("EMAIL_PORT")

# Define whether TLS (Transport Layer Security) should be used.
# Convert the environment variable from string to boolean.
EMAIL_USE_TLS: bool = True if os.environ.get("TLS") == "True" else False

# Get the username for SMTP server authentication from environment variables.
EMAIL_HOST_USER = os.environ.get("USER_CREDENTIAL_SMTP")

# Get the password for SMTP server authentication from environment variables.
EMAIL_HOST_PASSWORD = os.environ.get("PASSWORD_CREDENTIAL_SMTP")

# Get the default email address to be used as the sender in sent messages.
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_EMAIL")
"""
