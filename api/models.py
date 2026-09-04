"""
SkillSync - API Response Models (Pydantic)

These models define the shape of the JSON that our API returns.
Pydantic automatically validates the data and generates the
OpenAPI/Swagger documentation.

Why separate models for API responses vs. scraper models?
- Scraper models are for input validation (what goes INTO the database)
- API models are for output formatting (what comes OUT of the API)
- They may have different fields (e.g., API includes _id, scraper doesn't)
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ListingResponse(BaseModel):
    """
    A single listing as returned by the API.
    
    This is what the client sees when they hit GET /listings or GET /listings/{id}.
    """
    id: str = Field(..., description="MongoDB document ID")
    title: str = Field(..., description="Job/event title")
    source: str = Field(..., description="Platform name (e.g., 'rozee', 'devpost')")
    source_url: str = Field(..., description="Link to original listing")
    description_raw: str = Field(default="", description="Full description text")
    company: Optional[str] = Field(default=None, description="Company or organization")
    location: Optional[str] = Field(default=None, description="Job location or 'Remote'")
    posted_date: Optional[datetime] = Field(default=None, description="When posted")
    deadline: Optional[datetime] = Field(default=None, description="Application deadline")
    domain_tag: Optional[str] = Field(default=None, description="Domain (FYP-I)")
    skills: List[str] = Field(default_factory=list, description="Required skills (FYP-I)")
    scraped_at: datetime = Field(..., description="When this listing was scraped")
    is_active: bool = Field(default=True, description="Whether listing is still active")


class PaginatedResponse(BaseModel):
    """
    Paginated response wrapper.
    
    Wraps a list of listings with pagination metadata so the client
    knows how to navigate through results.
    
    Example response:
    {
        "listings": [...],
        "total": 150,
        "page": 1,
        "page_size": 20,
        "total_pages": 8
    }
    """
    listings: List[ListingResponse] = Field(..., description="List of listings")
    total: int = Field(..., description="Total number of matching listings")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of listings per page")
    total_pages: int = Field(..., description="Total number of pages")


class SourceInfo(BaseModel):
    """Information about a scraper source."""
    name: str = Field(..., description="Source platform name")
    total_listings: int = Field(..., description="Number of listings from this source")
    last_scraped: Optional[datetime] = Field(default=None, description="Last scrape time")


class ScrapeStatusResponse(BaseModel):
    """Status of the last scraper run for a specific source."""
    scraper_name: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    listings_found: int = 0
    listings_new: int = 0
    listings_failed: int = 0
    status: str = "unknown"
    errors: List[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="'ok' if the service is healthy")
    database: str = Field(..., description="'connected' or 'disconnected'")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
