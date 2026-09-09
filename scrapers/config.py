import os

from dotenv import load_dotenv

# Load .env file if it exists (for local development)
load_dotenv()


class ScraperConfig:
    """
    Configuration for the scraper service.
    All values come from environment variables with sensible defaults.
    """
    
    # MongoDB connection
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "skillsync")
    
    # Scheduling
    SCRAPE_INTERVAL_HOURS: int = int(os.getenv("SCRAPE_INTERVAL_HOURS", "12"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Selenium
    HEADLESS: bool = os.getenv("HEADLESS", "true").lower() == "true"
    
    # Optional: Rozee.pk session cookie
    ROZEE_SESSION_COOKIE: str = os.getenv("ROZEE_SESSION_COOKIE", "")
    
    # Collections
    LISTINGS_COLLECTION: str = "listings"
    SCRAPER_RUNS_COLLECTION: str = "scraper_runs"
             


# Global config instance
config = ScraperConfig()
