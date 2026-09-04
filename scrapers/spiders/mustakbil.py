"""
SkillSync - Mustakbil.com Scraper (BeautifulSoup)

Mustakbil.com is a Pakistani job portal. This scraper uses:
- requests: to download the HTML page
- BeautifulSoup: to parse the HTML and extract job data

This is a STATIC scraper — the page content is in the HTML source,
no JavaScript rendering needed (unlike Selenium scrapers).

NOTE: CSS selectors may need updating if the website changes its layout.
      Look for comments marked "SELECTOR:" to find what to update.
"""

from typing import List, Dict, Any
from datetime import datetime
import requests
from bs4 import BeautifulSoup

from scrapers.spiders.base import BaseScraper
from scrapers.utils import get_requests_headers, random_delay, clean_text


class MustakbilScraper(BaseScraper):
    """Scraper for Mustakbil.com internship listings."""
    
    # Base URL for internship listings on Mustakbil
    BASE_URL = "https://www.mustakbil.com/jobs?search=internship&page={page}"
    
    # How many pages to scrape per run
    MAX_PAGES = 3
    
    def __init__(self):
        super().__init__(name="mustakbil")
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape internship listings from Mustakbil.com.
        
        Iterates through multiple pages of search results,
        extracting job details from each listing card.
        
        Returns:
            List of raw listing dictionaries
        """
        all_listings = []
        
        for page_num in range(1, self.MAX_PAGES + 1):
            self.logger.info(f"Scraping page {page_num} of {self.MAX_PAGES}")
            
            url = self.BASE_URL.format(page=page_num)
            
            try:
                # Send HTTP request with rotating User-Agent
                response = requests.get(url, headers=get_requests_headers(), timeout=15)
                response.raise_for_status()  # Raise error for 4xx/5xx status codes
                
                # Parse the HTML content
                soup = BeautifulSoup(response.text, "lxml")
                
                # SELECTOR: Find all job listing cards on the page
                # Update this selector if Mustakbil changes their HTML structure
                job_cards = soup.select("div.job-listing, div.job-card, article.job")
                
                if not job_cards:
                    # Try alternative selectors
                    job_cards = soup.select("div[class*='job'], div[class*='listing']")
                
                if not job_cards:
                    self.logger.warning(f"No job cards found on page {page_num}. "
                                        "The website layout may have changed.")
                    continue
                
                # Extract data from each job card
                for card in job_cards:
                    listing = self._parse_card(card)
                    if listing:
                        all_listings.append(listing)
                
                self.logger.info(f"Page {page_num}: found {len(job_cards)} listings")
                
            except requests.RequestException as e:
                self.logger.error(f"Failed to fetch page {page_num}: {str(e)}")
            
            # Be polite - wait between page requests
            random_delay(1.5, 3.0)
        
        return all_listings
    
    def _parse_card(self, card: BeautifulSoup) -> Dict[str, Any] | None:
        """
        Extract listing data from a single job card HTML element.
        
        Args:
            card: BeautifulSoup element for one job card
            
        Returns:
            Dictionary with listing data, or None if parsing failed
        """
        try:
            # SELECTOR: Job title - usually in an <a> or <h2> tag
            title_elem = card.select_one("h2 a, h3 a, a.job-title, a[class*='title']")
            if not title_elem:
                return None
            
            title = clean_text(title_elem.get_text())
            
            # SELECTOR: Job URL
            source_url = title_elem.get("href", "")
            if source_url and not source_url.startswith("http"):
                source_url = "https://www.mustakbil.com" + source_url
            
            # SELECTOR: Company name
            company_elem = card.select_one("span.company, div.company-name, "
                                            "a[class*='company']")
            company = clean_text(company_elem.get_text()) if company_elem else None
            
            # SELECTOR: Location
            location_elem = card.select_one("span.location, div.job-location, "
                                             "span[class*='location']")
            location = clean_text(location_elem.get_text()) if location_elem else None
            
            # SELECTOR: Description/summary
            desc_elem = card.select_one("p.description, div.job-description, "
                                         "p[class*='desc']")
            description = clean_text(desc_elem.get_text()) if desc_elem else ""
            
            return {
                "title": title,
                "source_url": source_url,
                "description_raw": description,
                "company": company,
                "location": location,
                "posted_date": None,  # Parse if available on the page
                "deadline": None,
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to parse a job card: {str(e)}")
            return None
