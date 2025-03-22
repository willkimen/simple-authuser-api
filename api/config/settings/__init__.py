from pathlib import Path

from dotenv import load_dotenv

# Define the base path where the .env files are located
base_path = Path(__file__).resolve().parent.parent.parent

load_dotenv(base_path / "environments/.env")

from .development import *
