"""
SkillSync - Devpost Scraper (Selenium)

Devpost.com is a platform for hackathons and tech challenges.
The site uses JavaScript-rendered content, so we use Selenium.

We specifically scrape the hackathon listings page to find upcoming
tech events that students can participate in.

Devpost card structure (from live site inspection):
- Card container: a.tile-anchor (or .hackathon-tile)
- Title: h3 inside a.tile-anchor
- Host/Organizer: span.host-label
- Theme tags: span.theme-label
- Link URL: a.tile-anchor[href]

NOTE: CSS selectors may need updating if the website changes its layout.
      Look for comments marked "SELECTOR:" to find what to update.
"""

from typing import List, Dict, Any
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

from scrapers.spiders.base import BaseScraper
from scrapers.utils import create_selenium_driver, random_delay, clean_text


class DevpostScraper(BaseScraper):
    """
    Scraper for Devpost hackathon/challenge listings.
    Uses Selenium for JavaScript-rendered content.
    """
    
    # URL for hackathon listings on Devpost
    BASE_URL = "https://devpost.com/hackathons?page={page}&status[]=upcoming&status[]=open"
    
    # How many pages to scrape
    MAX_PAGES = 3
    
    def __init__(self):
        super().__init__(name="devpost")
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape hackathon listings from Devpost.
        
        Devpost lists hackathons in tile format. We look for
        upcoming and currently open hackathons.
        
        Returns:
            List of raw listing dictionaries
        """
        all_listings = []
        driver = None
        
        try:
            driver = create_selenium_driver()
            
            for page_num in range(1, self.MAX_PAGES + 1):
                self.logger.info(f"Scraping page {page_num} of {self.MAX_PAGES}")
                
                url = self.BASE_URL.format(page=page_num)
                driver.get(url)
                
                # Wait for hackathon tiles to load
                # SELECTOR: Main tile anchor elements
                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR,
                            "a.tile-anchor, div.hackathon-tile"))
                    )
                except Exception:
                    self.logger.warning(f"Page {page_num}: hackathon tiles did not load")
                    continue
                
                # Give page extra time to render
                random_delay(2.0, 3.0)
                
                # Parse with BeautifulSoup for easier extraction
                soup = BeautifulSoup(driver.page_source, "lxml")
                
                # SELECTOR: Find all hackathon tile anchors
                tiles = soup.select("a.tile-anchor")
                
                if not tiles:
                    # Fallback selectors
                    tiles = soup.select("div.hackathon-tile, div[class*='hackathon']")
                
                if not tiles:
                    self.logger.warning(f"No hackathon tiles found on page {page_num}")
                    continue
                
                for tile in tiles:
                    listing = self._parse_tile(tile)
                    if listing:
                        all_listings.append(listing)
                
                self.logger.info(f"Page {page_num}: found {len(tiles)} hackathons")
                
                random_delay(2.0, 4.0)
        
        except Exception as e:
            self.logger.error(f"Scraper FAILED with error: {str(e)}")
                
        finally:
            if driver:
                driver.quit()
                self.logger.info("Browser closed")
        
        return all_listings
    
    def _parse_tile(self, tile) -> Dict[str, Any] | None:
        """
        Extract hackathon data from a Devpost tile element.
        
        Devpost tile structure (from live site):
        - a.tile-anchor: the entire card is a link
        - h3: hackathon title
        - span.host-label: organizer name
        - span.theme-label: theme/interest tags
        
        Args:
            tile: BeautifulSoup element for one hackathon tile
            
        Returns:
            Dictionary with listing data, or None if parsing failed
        """
        try:
            # SELECTOR: Hackathon title — h3 inside the tile
            title_elem = tile.select_one("h3, h2")
            if not title_elem:
                return None
            
            title = clean_text(title_elem.get_text())
            if not title:
                return None
            
            # SELECTOR: Hackathon URL — href on the tile anchor
            source_url = tile.get("href", "")
            if source_url and not source_url.startswith("http"):
                source_url = "https://devpost.com" + source_url
            
            # SELECTOR: Organization/host — span.host-label
            company = None
            host_elem = tile.select_one("span.host-label, span[class*='host']")
            if host_elem:
                company = clean_text(host_elem.get("title", "") or host_elem.get_text())
            
            # SELECTOR: Theme tags — span.theme-label
            themes = []
            theme_elems = tile.select("span.theme-label, span[class*='theme']")
            for t in theme_elems:
                themes.append(clean_text(t.get_text()))
            
            # SELECTOR: Location
            location = "Online"  # Most Devpost hackathons are online
            loc_elem = tile.select_one("span[class*='location'], span[class*='venue']")
            if loc_elem:
                location = clean_text(loc_elem.get_text()) or "Online"
            
            # SELECTOR: Prize/description info
            description_parts = []
            if company:
                description_parts.append(f"Hosted by {company}")
            if themes:
                description_parts.append(f"Themes: {', '.join(themes)}")
            
            # Look for prize amount text
            prize_elem = tile.find(string=lambda t: t and "in prizes" in t.lower() if t else False)
            if prize_elem:
                description_parts.append(clean_text(prize_elem))
            
            description = ". ".join(description_parts) if description_parts else f"Hackathon on Devpost: {title}"
            
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
            self.logger.warning(f"Failed to parse a hackathon tile: {str(e)}")
            return None
