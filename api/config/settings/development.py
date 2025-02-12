from .base import *

# Debugging mode on for development
# -----------------------------------------------------------------------------
DEBUG = True


# Development secret key
# -----------------------------------------------------------------------------
SECRET_KEY = "secret_insecure_jldsfj5165ser5wg16ae5344*"
TOKEN_SECRET = "secret_token_insecure_jldsfj51dfsd65fsklj564564wg16ae5344*"


# Allowed hosts and allowed origins for development
# -----------------------------------------------------------------------------
ALLOWED_HOSTS: list[str] = []
CORS_ALLOWED_ORIGINS: list[str] = []


# Redirect links
# -----------------------------------------------------------------------------
RESET_PASSWORD_LINK = "domain.com/reset/password/"
ACTIVATE_ACCOUNT_LINK = "domain.com/confirmation/email/"
LOGIN_LINK = "domain.com/login/"


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
