import os
from pathlib import Path

# Diretório base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Segurança
# -----------------------------------------------------------------------------
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "ENV_SECRET_KEY", "secret_insecure_jldsfj5165ser5wg16ae5344*"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# -----  Hosts permitidos -----
ALLOWED_HOSTS: list[str] = [
    host.strip() for host in os.environ.get("ENV_ALLOWED_HOSTS", "").split(",")
]

# ---- Cors ----
CORS_ALLOWED_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.environ.get("ENV_CORS_ALLOWED_ORIGINS", "").split(",")
]

# Aplicativos instalados
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

# Configurações de URLs
# -----------------------------------------------------------------------------
ROOT_URLCONF = "config.urls"

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

# Banco de dados
# -----------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Configuraçao para desenvolver com container postgres
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

# Validação de senhas
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

# Configuração do modelo de usuário
# -----------------------------------------------------------------------------
AUTH_USER_MODEL = "user_app.UserProfile"

# Internacionalização
# -----------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Arquivos estáticos
# -----------------------------------------------------------------------------
STATIC_URL = "static/"

# Configuração do campo auto incrementado padrão
# -----------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Configurações para envio de email
# -----------------------------------------------------------------------------

# Define o backend de email a ser usado pelo Django. Neste caso, o backend SMTP.
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# Obtém o host do servidor SMTP a partir das variáveis de ambiente.
EMAIL_HOST = os.environ.get("ENV_EMAIL_HOST")

# Obtém a porta do servidor SMTP a partir das variáveis de ambiente.
EMAIL_PORT = os.environ.get("ENV_EMAIL_PORT")

# Define se o TLS (Transport Layer Security) deve ser usado. Converte a variável de ambiente de string para booleano.
EMAIL_USE_TLS: bool = True if os.environ.get("ENV_EMAIL_USE_TLS") == "True" else False

# Obtém o nome de usuário para autenticação no servidor SMTP a partir das variáveis de ambiente.
EMAIL_HOST_USER = os.environ.get("ENV_EMAIL_HOST_USE")

# Obtém a senha para autenticação no servidor SMTP a partir das variáveis de ambiente.
EMAIL_HOST_PASSWORD = os.environ.get("ENV_EMAIL_HOST_PASSWORD")

# Obtém o endereço de email padrão a ser usado como remetente nas mensagens enviadas.
DEFAULT_FROM_EMAIL = os.environ.get("ENV_DEFAULT_FROM_EMAIL")
