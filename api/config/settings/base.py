import logging
from pathlib import Path

from user_app.constants.logs_constants import (
    EMAIL_TASK_ERROR_LEVEL,
    EMAIL_TASK_ERROR_LEVEL_NAME,
    EMAIL_TASK_ERROR_LOGGER_NAME,
)

# Project base directory
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent


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
    "django_celery_beat",
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


# Root URLs and WSGI
# -----------------------------------------------------------------------------
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"


# Rest Framework Configurations
# -----------------------------------------------------------------------------
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "user_app.custom_exception_handler.custom_exception_handler",
}


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


# Logging
# -----------------------------------------------------------------------------
# Add level to logging system
logging.addLevelName(EMAIL_TASK_ERROR_LEVEL, EMAIL_TASK_ERROR_LEVEL_NAME)


# Create a custom method for the logger
def email_task_error(self, message, *args, **kwargs):
    if self.isEnabledFor(EMAIL_TASK_ERROR_LEVEL):
        self._log(EMAIL_TASK_ERROR_LEVEL, message, args, **kwargs)


# Add the method to the logger
logging.Logger.email_task_error = email_task_error

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose_multiline": {
            "format": "{levelname} {asctime} {module} {funcName}\n{message}",
            "style": "{",
        },
    },
    "handlers": {
        "email_task_error_file": {
            "level": EMAIL_TASK_ERROR_LEVEL,
            "class": "logging.FileHandler",
            "filename": "logs/email_task_errors.log",
            "formatter": "verbose_multiline",
        },
    },
    "loggers": {
        EMAIL_TASK_ERROR_LOGGER_NAME: {
            "handlers": ["email_task_error_file"],
            "level": EMAIL_TASK_ERROR_LEVEL,
            "propagate": True,
        },
    },
}

# Verification code configuration
# -----------------------------------------------------------------------------
EXPIRATION_CODE_TIME_IN_HOURS = 24


# Static files
# -----------------------------------------------------------------------------
STATIC_URL = "static/"


# Default auto field configuration
# -----------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Configuration Celery
# -----------------------------------------------------------------------------
# CELERY_BROKER_URL specifies the broker URL for Celery.
# In this case, "redis_broker" refers to the name of the Docker container running Redis.
# Make sure the container is named "redis_broker" in your Docker Compose.
CELERY_BROKER_URL = "redis://redis_broker:6379/0"
CELERY_RESULT_BACKEND = "redis://redis_broker:6379/1"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
