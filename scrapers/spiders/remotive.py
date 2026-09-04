"""
SkillSync - Remotive Scraper (JSON API)

Remotive.com provides a PUBLIC JSON API for their job listings.
This is the simplest scraper — no HTML parsing needed!

We just send an HTTP request to their API endpoint and get back
structured JSON data. No Selenium, no BeautifulSoup needed.

API endpoint: https://remotive.com/api/remote-jobs
Documentation: https://remotive.com/api/remote-jobs?limit=5 (try it in your browser)
"""

from typing import List, Dict, Any
from datetime import datetime
import requests

from scrapers.spiders.base import BaseScraper
from scrapers.utils import get_requests_headers, clean_text


class RemotiveScraper(BaseScraper):
    """
    Scraper for Remotive.com remote job listings.
    Uses their public JSON API — no HTML parsing required.
    """
    
    # Remotive's public API endpoint
    API_URL = "https://remotive.com/api/remote-jobs"
    
    # Filter for tech/software categories relevant to CS students
    CATEGORIES = ["software-dev", "data", "devops", "product", "qa"]
    
    def __init__(self):
        super().__init__(name="remotive")
    
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Fetch job listings from Remotive's JSON API.
        
        The API returns a JSON object with a 'jobs' array.
        Each job has fields like title, company_name, url, description, etc.
        
        Returns:
            List of raw listing dictionaries
        """
        all_listings = []
        
        for category in self.CATEGORIES:
            self.logger.info(f"Fetching Remotive listings for category: {category}")
            
            try:
                # Send request to the API with category filter
                params = {
                    "category": category,
                    "limit": 50,  # Max listings per category
                }
                
                response = requests.get(
                    self.API_URL, 
                    params=params,
                    headers=get_requests_headers(), 
                    timeout=15
                )
                response.raise_for_status()
                
                # Parse JSON response
                data = response.json()
                jobs = data.get("jobs", [])
                
                self.logger.info(f"Category '{category}': found {len(jobs)} listings")
                
                # Convert each job to our listing format
                for job in jobs:
                    listing = self._parse_job(job)
                    if listing:
                        all_listings.append(listing)
                        
            except requests.RequestException as e:
                self.logger.error(f"Failed to fetch category '{category}': {str(e)}")
            except ValueError as e:
                self.logger.error(f"Failed to parse JSON for '{category}': {str(e)}")
        
        return all_listings
    
    def _parse_job(self, job: dict) -> Dict[str, Any] | None:
        """
        Convert a Remotive API job object to our listing format.
        
        Remotive API returns fields like:
        - title, company_name, url, description
        - publication_date, candidate_required_location
        - category, job_type, salary
        
        Args:
            job: Dictionary from Remotive's API response
            
        Returns:
            Dictionary in our listing format, or None if data is incomplete
        """
        try:
            title = clean_text(job.get("title", ""))
            if not title:
                return None
            
            # Parse the publication date
            posted_date = None
            date_str = job.get("publication_date", "")
            if date_str:
                try:
                    # Remotive uses ISO format dates
                    posted_date = datetime.fromisoformat(
                        date_str.replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    pass
            
            return {
                "title": title,
                "source_url": job.get("url", ""),
                "description_raw": clean_text(job.get("description", "")),
                "company": clean_text(job.get("company_name", "")) or None,
                "location": clean_text(
                    job.get("candidate_required_location", "Remote")
                ),
                "posted_date": posted_date,
                "deadline": None,  # Remotive doesn't provide deadlines
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to parse Remotive job: {str(e)}")
            return None
