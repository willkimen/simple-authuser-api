import os
from pathlib import Path

from dotenv import load_dotenv

# Define constants for development and production environments
DEVELOPMENT = "development"
PRODUCTION = "production"

# Define the base path where the .env files are located
base_path = Path(__file__).resolve().parent.parent.parent

# Load environment variables from the .env.base file
load_dotenv(base_path / "environments/.env.base")

# Get the current environment, defaulting to 'development' if 'DJANGO_ENV' is not set
ENVIRONMENT = os.environ.get("DJANGO_ENV", DEVELOPMENT)

# Check if the environment is production
if ENVIRONMENT == PRODUCTION:
    # Load environment variables from the .env.production file
    load_dotenv(base_path / "environments/.env.production")
    # Import production-specific settings
    from .production import *
else:
    # Load environment variables from the .env.development file
    load_dotenv(base_path / "environments/.env.development")
    # Import development-specific settings
    from .development import *
