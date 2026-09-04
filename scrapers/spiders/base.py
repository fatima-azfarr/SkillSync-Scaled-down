"""
SkillSync - Base Scraper Class

All 6 scrapers inherit from this base class. It provides:
- A common interface (every scraper must implement the scrape() method)
- Automatic error handling (one scraper failing doesn't crash the others)
- Logging hooks for start/end of each run

This is a simple use of Python's OOP (Object-Oriented Programming):
- BaseScraper is an abstract base class
- Each platform scraper extends it and provides its own scrape() logic
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from scrapers.logger import get_logger, log_scraper_start


class BaseScraper(ABC):
    """
    Abstract base class for all scrapers.
    
    Every scraper must:
    1. Set self.name (e.g., "rozee", "devpost")
    2. Implement the scrape() method
    3. Return a list of raw listing dictionaries
    
    The base class handles:
    - Error catching (so one scraper failing doesn't crash others)
    - Logging
    """
    
    def __init__(self, name: str):
        """
        Initialize the scraper.
        
        Args:
            name: Unique name for this scraper (e.g., "rozee")
        """
        self.name = name
        self.logger = get_logger(f"scraper.{name}")
    
    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape listings from the platform.
        
        Each scraper implements this method with its own logic
        (BeautifulSoup, Selenium, or API calls).
        
        Returns:
            List of raw listing dictionaries with at minimum:
            - title: str
            - source_url: str
            - description_raw: str (can be empty)
            
            Optional fields:
            - company: str
            - location: str
            - posted_date: datetime
            - deadline: datetime
        """
        pass
    
    def run(self) -> List[Dict[str, Any]]:
        """
        Execute the scraper with error handling.
        
        This is the method called by the scheduler. It wraps scrape()
        in a try-except so that if this scraper fails, the error is
        logged but not raised — other scrapers continue running.
        
        Returns:
            List of raw listings, or empty list if scraper failed
        """
        log_scraper_start(self.logger, self.name)
        
        try:
            listings = self.scrape()
            self.logger.info(f"Scraping complete. Found {len(listings)} listings.")
            return listings
            
        except Exception as e:
            # Catch ALL exceptions — this scraper failing must NOT
            # prevent the other 5 scrapers from running
            self.logger.error(f"Scraper FAILED with error: {str(e)}")
            return []
