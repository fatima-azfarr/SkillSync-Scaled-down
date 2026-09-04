"""
SkillSync - Scraper Utilities

Common helper functions used across all scrapers:
- User-Agent rotation (to avoid being detected as a bot)
- Random delays between requests (politeness + anti-detection)
- Selenium WebDriver setup with automatic ChromeDriver management
"""

import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from scrapers.config import config

# List of common User-Agent strings to rotate through
# This makes our scraper look like different browsers to the target websites
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]


def get_random_user_agent() -> str:
    """Pick a random User-Agent string from our list."""
    return random.choice(USER_AGENTS)


def random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0):
    """
    Wait a random amount of time between requests.
    
    This serves two purposes:
    1. Politeness - we don't hammer the server with rapid requests
    2. Anti-detection - random delays look more like human browsing
    
    Args:
        min_seconds: Minimum wait time
        max_seconds: Maximum wait time
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def get_requests_headers() -> dict:
    """
    Get headers for requests-based scrapers (BeautifulSoup).
    Includes a random User-Agent to avoid bot detection.
    """
    return {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }


def create_selenium_driver() -> webdriver.Chrome:
    """
    Create and return a configured Selenium Chrome WebDriver.
    
    In Docker:  Uses system Chromium + chromedriver (set via env vars)
    Locally:    Uses webdriver-manager to auto-download ChromeDriver
    
    The driver is configured for scraping:
    - Headless mode (no visible browser window)
    - Random User-Agent
    - Various anti-detection flags
    
    Returns:
        A configured Chrome WebDriver instance
    """
    import os
    
    chrome_options = Options()
    
    # Run in headless mode (no visible browser window)
    if config.HEADLESS:
        chrome_options.add_argument("--headless=new")
    
    # Anti-detection settings
    chrome_options.add_argument(f"--user-agent={get_random_user_agent()}")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Performance: disable images and unnecessary features
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Disable the "Chrome is being controlled by automated software" bar
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Check if running in Docker (system Chromium available)
    chrome_bin = os.environ.get("CHROME_BIN")
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH")
    
    if chrome_bin and chromedriver_path:
        # Docker: use system-installed Chromium and chromedriver
        chrome_options.binary_location = chrome_bin
        service = Service(executable_path=chromedriver_path)
    else:
        # Local development: use webdriver-manager to auto-download
        service = Service(ChromeDriverManager().install())
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Set page load timeout to 30 seconds
    driver.set_page_load_timeout(30)
    
    return driver


def clean_text(text: str) -> str:
    """
    Basic text cleaning for scraped content.
    
    - Strips leading/trailing whitespace
    - Normalizes multiple spaces to single space
    - Removes null bytes and other problematic characters
    
    Args:
        text: Raw text from scraping
        
    Returns:
        Cleaned text string
    """
    if not text:
        return ""
    
    # Strip whitespace
    text = text.strip()
    
    # Replace multiple spaces/newlines with single space
    text = " ".join(text.split())
    
    # Remove null bytes (can cause issues with MongoDB)
    text = text.replace("\x00", "")
    
    return text
