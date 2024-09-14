import os
from pathlib import Path

# Project base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
# -----------------------------------------------------------------------------
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "ENV_SECRET_KEY", "secret_insecure_jldsfj5165ser5wg16ae5344*"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# ----- Allowed hosts -----
ALLOWED_HOSTS: list[str] = [
    host.strip() for host in os.environ.get("ENV_ALLOWED_HOSTS", "").split(",")
]

# ---- Cors ----
CORS_ALLOWED_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.environ.get("ENV_CORS_ALLOWED_ORIGINS", "").split(",")
]

# Installed apps
# -----------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "user_app",
]

# Middleware
# -----------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# URL configurations
# -----------------------------------------------------------------------------
ROOT_URLCONF = "config.urls"

# Rest Framework Configurations
# -----------------------------------------------------------------------------
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "user_app.custom_exception_handler.custom_exception_handler",
}

# Templates
# -----------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# WSGI
# -----------------------------------------------------------------------------
WSGI_APPLICATION = "config.wsgi.application"

# Database
# -----------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Configuration for developing with PostgreSQL container
"""
DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE"),
        "NAME": os.environ.get("POSTGRES_DB"),
        "USER": os.environ.get("POSTGRES_USER"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        "HOST": os.environ.get("POSTGRES_HOST"),
        "PORT": os.environ.get("POSTGRES_PORT"),
    }
}
"""

# Password validation
# -----------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# User model configuration
# -----------------------------------------------------------------------------
AUTH_USER_MODEL = "user_app.UserProfileModel"

# Internationalization
# -----------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
# -----------------------------------------------------------------------------
STATIC_URL = "static/"

# Default auto field configuration
# -----------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email settings
# -----------------------------------------------------------------------------

# Define the email backend to be used by Django. In this case, the SMTP backend.
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# Get the SMTP server host from environment variables.
EMAIL_HOST = os.environ.get("ENV_EMAIL_HOST")

# Get the SMTP server port from environment variables.
EMAIL_PORT = os.environ.get("ENV_EMAIL_PORT")

# Define whether TLS (Transport Layer Security) should be used. Convert the environment variable from string to boolean.
EMAIL_USE_TLS: bool = True if os.environ.get("ENV_EMAIL_USE_TLS") == "True" else False

# Get the username for SMTP server authentication from environment variables.
EMAIL_HOST_USER = os.environ.get("ENV_EMAIL_HOST_USER")

# Get the password for SMTP server authentication from environment variables.
EMAIL_HOST_PASSWORD = os.environ.get("ENV_EMAIL_HOST_PASSWORD")

# Get the default email address to be used as the sender in sent messages.
DEFAULT_FROM_EMAIL = os.environ.get("ENV_DEFAULT_FROM_EMAIL")
