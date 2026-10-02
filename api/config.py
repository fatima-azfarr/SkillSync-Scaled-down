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
    @property
    def MONGO_URI(self) -> str:
        return os.getenv("MONGO_URI", "mongodb://localhost:27017")

    @property
    def DATABASE_NAME(self) -> str:
        return os.getenv("DATABASE_NAME", "skillsync")

    
    # API settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Collection names
    LISTINGS_COLLECTION: str = "listings"
    SCRAPER_RUNS_COLLECTION: str = "scraper_runs"
    STUDENTS_COLLECTION: str = "students"

    # Security & Authentication settings
    # In production, JWT_SECRET_KEY must be provided via environment variable
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "skillsync_super_secure_jwt_dev_secret_key_change_in_prod_2026")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))  # 2 hours
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", "15"))  # 15 minutes
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = int(os.getenv("EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS", "24"))  # 24 hours

    # Rate Limiting settings
    RATE_LIMIT_LOGIN_MAX_ATTEMPTS: int = int(os.getenv("RATE_LIMIT_LOGIN_MAX_ATTEMPTS", "5"))
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_LOGIN_WINDOW_SECONDS", "900"))  # 15 minutes
    RATE_LIMIT_RESET_MAX_ATTEMPTS: int = int(os.getenv("RATE_LIMIT_RESET_MAX_ATTEMPTS", "3"))
    RATE_LIMIT_RESET_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_RESET_WINDOW_SECONDS", "900"))  # 15 minutes
    RATE_LIMIT_VERIFY_MAX_ATTEMPTS: int = int(os.getenv("RATE_LIMIT_VERIFY_MAX_ATTEMPTS", "3"))
    RATE_LIMIT_VERIFY_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_VERIFY_WINDOW_SECONDS", "900"))  # 15 minutes

    # CORS settings (never allow wildcard with credentials)
    CORS_ALLOWED_ORIGINS: list = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ALLOWED_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000,http://localhost:5500,http://127.0.0.1:5500,http://localhost:8080,http://127.0.0.1:8080"
        ).split(",")
        if origin.strip()
    ]


# Global config instance
config = APIConfig()
