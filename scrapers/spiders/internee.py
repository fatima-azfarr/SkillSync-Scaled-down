"""
SkillSync - Internee.pk Scraper (Selenium)

Internee.pk is a Pakistani virtual internship platform. It uses Next.js
to render content, so we need Selenium.

The scraper tries multiple URL paths and discovery strategies because
Internee.pk has changed their page structure multiple times.

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


class InterneeScraper(BaseScraper):
    """Scraper for Internee.pk virtual internship listings."""
    
    # Multiple URLs to try — Internee.pk has changed structure before
    URLS = [
        "https://www.internee.pk/",
        "https://internee.pk/",
    ]
    
    def __init__(self):
        super().__init__(name="internee")
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape internship listings from Internee.pk using Selenium.
        Tries multiple strategies to find internship cards.
        """
        all_listings = []
        driver = None
        
        try:
            driver = create_selenium_driver()
            
            for url in self.URLS:
                self.logger.info(f"Trying URL: {url}")
                
                try:
                    driver.get(url)
                except Exception as e:
                    self.logger.warning(f"Failed to load {url}: {str(e)}")
                    continue
                
                # Wait for page to fully render
                random_delay(4.0, 6.0)
                
                # Scroll down to trigger lazy loading
                for _ in range(5):
                    driver.execute_script("window.scrollBy(0, 600);")
                    random_delay(0.8, 1.5)
                
                # Scroll back to top
                driver.execute_script("window.scrollTo(0, 0);")
                random_delay(1.0, 1.5)
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(driver.page_source, "lxml")
                page_text = soup.get_text()
                
                self.logger.info(f"Page loaded. Text length: {len(page_text)}")
                
                # Strategy 1: Find all links to /internship/ pages
                internship_links = soup.select("a[href*='/internship/']")
                if internship_links:
                    self.logger.info(f"Strategy 1: Found {len(internship_links)} internship links")
                    seen_titles = set()
                    for link in internship_links:
                        listing = self._parse_internship_link(link, seen_titles)
                        if listing:
                            all_listings.append(listing)
                
                # Strategy 2: Find cards with group class
                if not all_listings:
                    cards = soup.select("div.group, div[class*='card'], div[class*='Card']")
                    if cards:
                        self.logger.info(f"Strategy 2: Found {len(cards)} card elements")
                        for card in cards:
                            listing = self._parse_card(card)
                            if listing:
                                all_listings.append(listing)
                
                # Strategy 3: Find headings that look like internship titles
                if not all_listings:
                    headings = soup.select("h2, h3, h4")
                    internship_keywords = ["development", "design", "data", "ai", "ml", 
                                           "web", "app", "backend", "frontend", "devops",
                                           "intern", "python", "java", "react"]
                    for h in headings:
                        text = clean_text(h.get_text())
                        if text and any(kw in text.lower() for kw in internship_keywords):
                            # Find nearest link
                            parent = h.parent
                            link = parent.select_one("a") if parent else None
                            href = link.get("href", "") if link else ""
                            if href and not href.startswith("http"):
                                href = "https://www.internee.pk" + href
                            
                            all_listings.append({
                                "title": text + (" Internship" if "intern" not in text.lower() else ""),
                                "source_url": href or f"https://www.internee.pk/",
                                "description_raw": f"Virtual {text} program on Internee.pk",
                                "company": "Internee.pk",
                                "location": "Remote, Pakistan",
                                "posted_date": None,
                                "deadline": None,
                            })
                
                if all_listings:
                    break  # Found listings, no need to try next URL
            
            self.logger.info(f"Found {len(all_listings)} internship listings")
            
        except Exception as e:
            self.logger.error(f"Scraper FAILED with error: {str(e)}")
            
        finally:
            if driver:
                driver.quit()
                self.logger.info("Browser closed")
        
        return all_listings
    
    def _parse_internship_link(self, link, seen_titles: set) -> Dict[str, Any] | None:
        """Parse an internship from an <a> tag with href containing /internship/."""
        try:
            # Get text — could be "Apply Now" or the actual title
            text = clean_text(link.get_text())
            href = link.get("href", "")
            
            if not href:
                return None
            
            if not href.startswith("http"):
                href = "https://www.internee.pk" + href
            
            # If the link text is generic ("Apply Now", "View"), try to get title from context
            if not text or len(text) < 4 or text.lower() in ["apply now", "apply", "view", "learn more"]:
                # Try parent elements for a better title
                parent = link.parent
                for _ in range(3):
                    if not parent:
                        break
                    heading = parent.select_one("h2, h3, h4, h5")
                    if heading:
                        text = clean_text(heading.get_text())
                        break
                    parent = parent.parent
            
            if not text or len(text) < 3:
                # Extract title from URL slug
                slug = href.split("/internship/")[-1].strip("/").split("?")[0]
                if slug and len(slug) > 5:
                    text = slug.replace("-", " ").title()
            
            if not text or len(text) < 3:
                return None
            
            # Deduplicate
            if text.lower() in seen_titles:
                return None
            seen_titles.add(text.lower())
            
            return {
                "title": text + (" Internship" if "intern" not in text.lower() else ""),
                "source_url": href,
                "description_raw": f"Virtual {text} internship on Internee.pk",
                "company": "Internee.pk",
                "location": "Remote, Pakistan",
                "posted_date": None,
                "deadline": None,
            }
        except Exception:
            return None
    
    def _parse_card(self, card) -> Dict[str, Any] | None:
        """Parse an internship from a card div."""
        try:
            title_elem = card.select_one("h3, h2, h4, h5")
            if not title_elem:
                return None
            
            title = clean_text(title_elem.get_text())
            if not title or len(title) < 3:
                return None
            
            link_elem = card.select_one("a[href*='/internship/'], a[href*='apply'], a")
            source_url = ""
            if link_elem:
                source_url = link_elem.get("href", "")
                if source_url and not source_url.startswith("http"):
                    source_url = "https://www.internee.pk" + source_url
            
            return {
                "title": title + (" Internship" if "intern" not in title.lower() else ""),
                "source_url": source_url or "https://www.internee.pk/",
                "description_raw": f"Virtual {title} internship on Internee.pk",
                "company": "Internee.pk",
                "location": "Remote, Pakistan",
                "posted_date": None,
                "deadline": None,
            }
        except Exception:
            return None
