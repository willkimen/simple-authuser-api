from .base import *

# Debugging mode off for production
# -----------------------------------------------------------------------------
DEBUG = False

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
RESET_LINK = os.environ.get("REDIRECT_TO_ACTIVATE_ACCOUNT_PAGE", "")
CONFIRMATION_LINK = os.environ.get("REDIRECT_TO_RESET_PASSWORD_PAGE", "")


# Database (usando PostgreSQL em produção)
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
