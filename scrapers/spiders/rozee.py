"""
SkillSync - Rozee.pk Scraper (Selenium)

Rozee.pk is Pakistan's largest job portal. It uses JavaScript-rendered content
(React app), so we need Selenium (a browser automation tool) to load pages.

This scraper also includes a cookie-reuse mechanism for handling CAPTCHAs.

NOTE: CSS selectors may need updating if the website changes its layout.
"""

from typing import List, Dict, Any
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

from scrapers.spiders.base import BaseScraper
from scrapers.utils import create_selenium_driver, random_delay, clean_text
from scrapers.config import config


class RozeeScraper(BaseScraper):
    """
    Scraper for Rozee.pk internship listings.
    Uses Selenium for JavaScript-rendered content.
    """
    
    # Search URL for internships on Rozee.pk
    BASE_URL = "https://www.rozee.pk/job/jsearch/q/internship/fc/cp/fpn/{page}"
    
    # How many pages to scrape
    MAX_PAGES = 3
    
    def __init__(self):
        super().__init__(name="rozee")
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape internship listings from Rozee.pk using Selenium.
        """
        all_listings = []
        driver = None
        
        try:
            driver = create_selenium_driver()
            
            # If a session cookie is configured, add it for CAPTCHA bypass
            if config.ROZEE_SESSION_COOKIE:
                self._add_session_cookie(driver)
            
            for page_num in range(1, self.MAX_PAGES + 1):
                self.logger.info(f"Scraping page {page_num} of {self.MAX_PAGES}")
                
                url = self.BASE_URL.format(page=page_num)
                driver.get(url)
                
                # Wait for page to load — be patient with JS rendering
                random_delay(5.0, 7.0)
                
                # Get full page source and parse with BS4
                soup = BeautifulSoup(driver.page_source, "lxml")
                page_text = soup.get_text()
                
                # Check for CAPTCHA
                if "captcha" in page_text.lower() or "verify" in page_text.lower()[:500]:
                    self.logger.warning(f"Page {page_num}: CAPTCHA detected, skipping")
                    continue
                
                # Try multiple selector strategies to find job cards
                listings_on_page = []
                
                # Strategy 1: Look for h3 > a links (job titles)
                job_headings = soup.select("h3 a")
                if job_headings:
                    self.logger.info(f"Strategy 1: Found {len(job_headings)} h3>a elements")
                    for link in job_headings:
                        listing = self._parse_h3_link(link)
                        if listing:
                            listings_on_page.append(listing)
                
                # Strategy 2: Look for links containing "-jobs-" in href
                if not listings_on_page:
                    job_links = soup.select("a[href*='-jobs-']")
                    if job_links:
                        self.logger.info(f"Strategy 2: Found {len(job_links)} job links")
                        for link in job_links:
                            listing = self._parse_job_link(link)
                            if listing:
                                listings_on_page.append(listing)
                
                # Strategy 3: Look for common job card patterns
                if not listings_on_page:
                    cards = soup.select("div.job, div[class*='jb'], div[class*='listing']")
                    if cards:
                        self.logger.info(f"Strategy 3: Found {len(cards)} card divs")
                        for card in cards:
                            title_link = card.select_one("a")
                            if title_link:
                                listing = self._parse_job_link(title_link)
                                if listing:
                                    listings_on_page.append(listing)
                
                if not listings_on_page:
                    # Log page title for debugging
                    title_tag = soup.select_one("title")
                    self.logger.warning(
                        f"No jobs found on page {page_num}. "
                        f"Page title: '{title_tag.get_text() if title_tag else 'N/A'}'. "
                        f"Page text length: {len(page_text)}"
                    )
                else:
                    all_listings.extend(listings_on_page)
                    self.logger.info(f"Page {page_num}: extracted {len(listings_on_page)} listings")
                
                random_delay(2.0, 4.0)
                
        except Exception as e:
            self.logger.error(f"Scraper FAILED with error: {str(e)}")
            
        finally:
            if driver:
                driver.quit()
                self.logger.info("Browser closed")
        
        return all_listings
    
    def _add_session_cookie(self, driver):
        """Add a session cookie to bypass CAPTCHA on Rozee.pk."""
        try:
            driver.get("https://www.rozee.pk")
            driver.add_cookie({
                "name": "PHPSESSID",
                "value": config.ROZEE_SESSION_COOKIE,
                "domain": ".rozee.pk"
            })
            self.logger.info("Session cookie added for CAPTCHA bypass")
        except Exception as e:
            self.logger.warning(f"Failed to set session cookie: {str(e)}")
    
    def _parse_h3_link(self, link_elem) -> Dict[str, Any] | None:
        """Parse a job listing from an h3 > a element."""
        try:
            title = clean_text(link_elem.get_text())
            if not title or len(title) < 3:
                return None
            
            source_url = link_elem.get("href", "")
            if source_url and not source_url.startswith("http"):
                source_url = "https://www.rozee.pk" + source_url
            if "?" in source_url:
                source_url = source_url.split("?")[0]
            
            # Try to find company/location in parent
            parent = link_elem.find_parent("div")
            company = None
            location = None
            if parent:
                inline_links = parent.select("a.display-inline")
                if len(inline_links) >= 1:
                    company = clean_text(inline_links[0].get_text())
                if len(inline_links) >= 2:
                    location = clean_text(inline_links[1].get_text())
            
            return {
                "title": title,
                "source_url": source_url,
                "description_raw": "",
                "company": company,
                "location": location or "Pakistan",
                "posted_date": None,
                "deadline": None,
            }
        except Exception:
            return None
    
    def _parse_job_link(self, link_elem) -> Dict[str, Any] | None:
        """Parse a job listing from any link element."""
        try:
            title = clean_text(link_elem.get_text())
            if not title or len(title) < 5:
                return None
            
            # Skip navigation/header links
            skip_words = ["login", "sign", "register", "about", "contact", "home", "search"]
            if any(w in title.lower() for w in skip_words):
                return None
            
            source_url = link_elem.get("href", "")
            if source_url and not source_url.startswith("http"):
                source_url = "https://www.rozee.pk" + source_url
            
            # Only accept links that look like job URLs
            if "-jobs-" not in source_url and "/job/" not in source_url:
                return None
            
            return {
                "title": title,
                "source_url": source_url,
                "description_raw": "",
                "company": None,
                "location": "Pakistan",
                "posted_date": None,
                "deadline": None,
            }
        except Exception:
            return None
