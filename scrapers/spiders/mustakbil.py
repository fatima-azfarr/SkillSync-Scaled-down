from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from scrapers.spiders.base import BaseScraper
from scrapers.utils import clean_text, get_requests_headers, random_delay


class MustakbilScraper(BaseScraper):
    """Scraper for Mustakbil.com internship/job listings via their JSON API."""

    API_URL = "https://api-public.mustakbil.com/ws/jobs/search/"
    COUNTRY_ID = 162  # Pakistan

    # Safety cap in case the API's hasMore flag ever misbehaves -
    # normally we stop as soon as hasMore is False.
    MAX_PAGES = 10

    def __init__(self):
        super().__init__(name="mustakbil")

    def scrape(self) -> List[Dict[str, Any]]:
        """
        Page through Mustakbil's job search API and return raw listings.

        Returns:
            List of raw listing dictionaries
        """
        all_listings = []
        page = 1

        while page <= self.MAX_PAGES:
            self.logger.info(f"Fetching page {page}")

            try:
                response = requests.get(
                    self.API_URL,
                    params={"countryid": self.COUNTRY_ID, "page": page},
                    headers=get_requests_headers(),
                    timeout=15,
                )
                response.raise_for_status()

            except requests.exceptions.HTTPError:
                if response.status_code == 429:
                    self.logger.warning("Rate limited. Waiting 10s before retry...")
                    random_delay(10, 12)
                    continue  # retry same page, don't increment
                self.logger.error(f"HTTP error on page {page}: {response.status_code}")
                break

            except requests.RequestException as e:
                self.logger.error(f"Failed to fetch page {page}: {str(e)}")
                break

            api_data = response.json()
            jobs = api_data.get("list", [])

            if not jobs:
                self.logger.info(f"No jobs on page {page}. Stopping.")
                break

            for job in jobs:
                listing = self._parse_job(job)
                if listing:
                    all_listings.append(listing)

            self.logger.info(f"Page {page}: found {len(jobs)} listings")

            if not api_data.get("hasMore", False):
                break

            random_delay(1.0, 2.0)  # be polite between pages
            page += 1

        return all_listings

    def _parse_job(self, job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Map a raw API job object to our standard listing dict.

        Args:
            job: One job object from the API's "list" array

        Returns:
            Dictionary with listing data, or None if a required field is missing
        """
        try:
            job_id = job.get("id")
            title = clean_text(job.get("title", ""))

            if not job_id or not title:
                return None

            # The API has no dedicated "remote" city string - telecommute
            # is a separate boolean, so build a readable location from it.
            if job.get("telecommute"):
                location = "Remote"
            else:
                location = clean_text(job.get("city") or job.get("cities") or "") or None

            return {
                "title": title,
                "source_url": f"https://www.mustakbil.com/jobs/job/{job_id}",
                "description_raw": clean_text(job.get("description", "")),
                "company": clean_text(job.get("company", "")) or None,
                "location": location,
                "posted_date": self._parse_api_datetime(job.get("postedOn")),
                "deadline": self._parse_api_datetime(job.get("lastDate")),
            }

        except Exception as e:
            self.logger.warning(f"Failed to parse a job entry: {str(e)}")
            return None

    @staticmethod
    def _parse_api_datetime(value: Optional[str]) -> Optional[datetime]:
        """
        Parse Mustakbil's timestamp format into a datetime.

        The API returns timestamps like "2026-08-24T23:45:29.0780520Z" -
        7 fractional-second digits plus a trailing "Z". Python's
        datetime.fromisoformat only accepts up to 6 fractional digits,
        so the extra digit has to be trimmed before parsing, and the
        trailing "Z" needs to be stripped since older/base fromisoformat
        implementations don't handle it directly.

        Args:
            value: Raw timestamp string from the API, or None

        Returns:
            Parsed datetime, or None if value is missing/unparseable
        """
        if not value:
            return None

        try:
            cleaned = value.rstrip("Z")
            if "." in cleaned:
                whole, frac = cleaned.split(".", 1)
                cleaned = f"{whole}.{frac[:6]}"  # truncate to microseconds
            return datetime.fromisoformat(cleaned)
        except (ValueError, AttributeError):
            return None