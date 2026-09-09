from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ListingSchema(BaseModel):
    """
    Schema for a single internship/hackathon/event listing.
    
    This is the core data model of SkillSync. Every scraper produces data
    that gets validated against this schema before storage.
    
    Fields marked Optional may not be available from all sources.
    """
    
    # Required fields - every listing must have these
    title: str = Field(..., min_length=1, description="Job/event title as scraped")
    source: str = Field(..., description="Platform name, e.g. 'rozee', 'devpost'")
    source_url: str = Field(..., description="Direct link to the original listing")
    description_raw: str = Field(default="", description="Full description text as scraped")
    
    # Optional fields - not all sources provide these
    posted_date: Optional[datetime] = Field(default=None, description="When the listing was posted")
    deadline: Optional[datetime] = Field(default=None, description="Application deadline, if any")
    location: Optional[str] = Field(default=None, description="Job location or 'Remote'")
    company: Optional[str] = Field(default=None, description="Company or organization name")
    
    # Fields populated in FYP-I (Phase 2) - empty for now
    domain_tag: Optional[str] = Field(default=None, description="Domain classification (FYP-I)")
    skills: List[str] = Field(default_factory=list, description="Extracted skills (FYP-I)")
    
    # Metadata
    scraped_at: datetime = Field(default_factory=datetime.utcnow, description="When this listing was scraped")
    is_active: bool = Field(default=True, description="False if listing disappeared on re-scrape")
    fingerprint: str = Field(default="", description="SHA-256 hash for deduplication")


class ScraperRunLog(BaseModel):
    """
    Logs metadata about each scraper run.
    Stored in a separate 'scraper_runs' collection for monitoring.
    """
    
    scraper_name: str = Field(..., description="Which scraper ran, e.g. 'rozee'")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = Field(default=None)
    listings_found: int = Field(default=0, description="Total raw listings scraped")
    listings_new: int = Field(default=0, description="Listings that passed dedup (new ones)")
    listings_failed: int = Field(default=0, description="Listings that failed validation")
    errors: List[str] = Field(default_factory=list, description="Any error messages during the run")
    status: str = Field(default="running", description="'running', 'success', or 'failed'")

