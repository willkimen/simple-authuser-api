import os
from pathlib import Path

from dotenv import load_dotenv

# Define the base path where the .env files are located
base_path = Path(__file__).resolve().parent.parent.parent

# Check if the environment is production
if os.getenv("API_ENV", "development") == "production":
    # Load environment variables from the .env.production file
    load_dotenv(base_path / "environments/.env.production")
    # Import production-specific settings
    from .production import *
else:
    # Load environment variables from the .env.development file
    load_dotenv(base_path / "environments/.env.development")
    # Import development-specific settings
    from .development import *
