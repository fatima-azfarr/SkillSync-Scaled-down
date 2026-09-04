"""
SkillSync - API Configuration

Loads API settings from environment variables using Pydantic BaseSettings.
This approach is recommended by FastAPI's documentation.

Why Pydantic BaseSettings?
- Automatically reads from environment variables
- Provides type validation
- Supports .env files via python-dotenv
- Gives us a single place to manage all configuration
"""

import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


class APIConfig:
    """
    API service configuration.
    All values come from environment variables with sensible defaults.
    """
    
    # MongoDB connection
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "skillsync")
    
    # API settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Collection names
    LISTINGS_COLLECTION: str = "listings"
    SCRAPER_RUNS_COLLECTION: str = "scraper_runs"


# Global config instance
config = APIConfig()
