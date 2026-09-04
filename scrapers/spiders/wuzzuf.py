"""
SkillSync - Wuzzuf.net Scraper (Selenium)

Wuzzuf.net is a Middle Eastern job portal. Uses Selenium because
Wuzzuf blocks plain HTTP requests with 403 Forbidden.

NOTE: CSS selectors may need updating if the website changes its layout.
"""

from typing import List, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup

from scrapers.spiders.base import BaseScraper
from scrapers.utils import create_selenium_driver, random_delay, clean_text


class WuzzufScraper(BaseScraper):
    """Scraper for Wuzzuf.net internship listings using Selenium."""
    
    BASE_URL = "https://wuzzuf.net/search/jobs/?q=internship&start={start}"
    MAX_PAGES = 3
    
    def __init__(self):
        super().__init__(name="wuzzuf")
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape internship listings from Wuzzuf.net using Selenium.
        """
        all_listings = []
        driver = None
        
        try:
            driver = create_selenium_driver()
            
            for page_num in range(0, self.MAX_PAGES):
                self.logger.info(f"Scraping page {page_num + 1} of {self.MAX_PAGES}")
                
                url = self.BASE_URL.format(start=page_num)
                
                try:
                    driver.get(url)
                    random_delay(4.0, 6.0)  # Wait for JS to render
                    
                    # Parse rendered HTML with BeautifulSoup
                    soup = BeautifulSoup(driver.page_source, "lxml")
                    page_text = soup.get_text()
                    
                    # Check for blocks/captcha
                    if len(page_text) < 500:
                        self.logger.warning(f"Page {page_num + 1}: Very short response, likely blocked")
                        continue
                    
                    # Strategy 1: Find job cards by class patterns
                    job_cards = soup.select(
                        "div.css-1gatmva, div.css-pkv5jg, "
                        "div[class*='JobCard'], div[class*='jobCard']"
                    )
                    
                    # Strategy 2: Broader selectors
                    if not job_cards:
                        job_cards = soup.select("div[class*='job'], article")
                    
                    # Strategy 3: Find all h2 > a links (Wuzzuf uses h2 for job titles)
                    if not job_cards:
                        title_links = soup.select("h2 a[href*='/jobs/'], a[href*='/jobs/p/']")
                        if title_links:
                            self.logger.info(f"Strategy 3: Found {len(title_links)} job links")
                            for link in title_links:
                                listing = self._parse_link(link)
                                if listing:
                                    all_listings.append(listing)
                            continue  # Already added, skip card parsing
                    
                    if not job_cards:
                        title_tag = soup.select_one("title")
                        self.logger.warning(
                            f"No job cards on page {page_num + 1}. "
                            f"Title: '{title_tag.get_text() if title_tag else 'N/A'}'"
                        )
                        continue
                    
                    for card in job_cards:
                        listing = self._parse_card(card)
                        if listing:
                            all_listings.append(listing)
                    
                    self.logger.info(f"Page {page_num + 1}: found {len(job_cards)} listings")
                    
                except Exception as e:
                    self.logger.error(f"Failed to scrape page {page_num + 1}: {str(e)}")
                
                random_delay(2.0, 4.0)
        
        except Exception as e:
            self.logger.error(f"Failed to create Selenium driver: {str(e)}")
        
        finally:
            if driver:
                driver.quit()
        
        return all_listings
    
    def _parse_card(self, card) -> Dict[str, Any] | None:
        """Extract listing data from a Wuzzuf job card."""
        try:
            title_elem = card.select_one("h2 a, a[class*='Title'], a[class*='title']")
            if not title_elem:
                return None
            
            title = clean_text(title_elem.get_text())
            if not title:
                return None
            
            source_url = title_elem.get("href", "")
            if source_url and not source_url.startswith("http"):
                source_url = "https://wuzzuf.net" + source_url
            
            company_elem = card.select_one("a[class*='Company'], span[class*='company']")
            company = clean_text(company_elem.get_text()) if company_elem else None
            
            location_elem = card.select_one("span[class*='Location'], span[class*='location']")
            location = clean_text(location_elem.get_text()) if location_elem else None
            
            desc_elem = card.select_one("div[class*='Description'], p[class*='desc']")
            description = clean_text(desc_elem.get_text()) if desc_elem else ""
            
            return {
                "title": title,
                "source_url": source_url,
                "description_raw": description,
                "company": company,
                "location": location,
                "posted_date": None,
                "deadline": None,
            }
        except Exception as e:
            self.logger.warning(f"Failed to parse a job card: {str(e)}")
            return None
    
    def _parse_link(self, link) -> Dict[str, Any] | None:
        """Parse a job listing from a link element."""
        try:
            title = clean_text(link.get_text())
            if not title or len(title) < 5:
                return None
            
            source_url = link.get("href", "")
            if source_url and not source_url.startswith("http"):
                source_url = "https://wuzzuf.net" + source_url
            
            return {
                "title": title,
                "source_url": source_url,
                "description_raw": "",
                "company": None,
                "location": None,
                "posted_date": None,
                "deadline": None,
            }
        except Exception:
            return None
