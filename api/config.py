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
    STUDENTS_COLLECTION: str = "students" 


# Global config instance
config = APIConfig()
