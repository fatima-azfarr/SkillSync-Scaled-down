"""
SkillSync - Structured Logger

Provides consistent, structured logging across all scrapers and the pipeline.
Uses Python's built-in logging module (no external dependencies).

Each log entry includes:
- Timestamp
- Logger name (which scraper or component)
- Log level (INFO, WARNING, ERROR)
- Message

Usage:
    from scrapers.logger import get_logger
    logger = get_logger("rozee_scraper")
    logger.info("Scraping started")
    logger.error("Failed to load page", extra={"url": "..."})
"""

import logging
import sys
from datetime import datetime


def get_logger(name: str) -> logging.Logger:
    """
    Create and return a configured logger.
    
    Args:
        name: Name for the logger (e.g., 'rozee_scraper', 'pipeline')
        
    Returns:
        A configured logging.Logger instance
    """
    logger = logging.getLogger(f"skillsync.{name}")
    
    # Avoid adding duplicate handlers if logger already exists
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Console handler - outputs to terminal
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Format: [timestamp] [LEVEL] [logger_name] message
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def log_scraper_start(logger: logging.Logger, scraper_name: str):
    """Log the start of a scraper run with a clear separator."""
    logger.info("=" * 50)
    logger.info(f"SCRAPER START: {scraper_name}")
    logger.info(f"Time: {datetime.utcnow().isoformat()}")
    logger.info("=" * 50)


def log_scraper_end(logger: logging.Logger, scraper_name: str, 
                    found: int, new: int, errors: int):
    """Log the end of a scraper run with summary statistics."""
    logger.info("-" * 50)
    logger.info(f"SCRAPER END: {scraper_name}")
    logger.info(f"  Listings found: {found}")
    logger.info(f"  New (after dedup): {new}")
    logger.info(f"  Errors: {errors}")
    logger.info("-" * 50)
