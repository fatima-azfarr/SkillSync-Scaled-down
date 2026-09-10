from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


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

class StudentRegister(BaseModel):
    """Request body for POST /students/register."""
    name: str = Field(..., min_length=1, description="Student's full name")
    first_name: Optional[str] = Field(default=None, description="Student's first name")
    last_name: Optional[str] = Field(default=None, description="Student's last name")
    email: EmailStr = Field(..., description="Student's email - must be unique")
    password: str = Field(..., min_length=8,
                           description="Plaintext password (min 8 chars) - hashed before storage")
    skills: List[str] = Field(default_factory=list, description="Initial skill list, from the taxonomy")
    preferred_domain: Optional[str] = Field(default=None, description="e.g. 'web development'")
    preferred_location: Optional[str] = Field(default=None, description="Preferred location, or 'Remote'")
    university: Optional[str] = Field(default=None, description="University or institution name")
    field_of_study: Optional[str] = Field(default=None, description="e.g. 'Computer Science'")
    domain_interests: List[str] = Field(default_factory=list, description="List of domain interests")


class StudentLogin(BaseModel):
    """Request body for POST /students/login."""
    email: EmailStr
    password: str


class StudentSkillsUpdate(BaseModel):
    """Request body for PUT /students/{id}/skills."""
    skills: List[str] = Field(default_factory=list, description="Replacement skill list")


class StudentPreferencesUpdate(BaseModel):
    """Request body for PUT /students/{id}/preferences."""
    preferred_domain: Optional[str] = Field(default=None, description="e.g. 'web development'")
    preferred_location: Optional[str] = Field(default=None, description="Preferred location, or 'Remote'")


class StudentProfileUpdate(BaseModel):
    """Request body for PUT /students/{id}/profile."""
    name: Optional[str] = Field(default=None, description="Full name")
    first_name: Optional[str] = Field(default=None, description="First name")
    last_name: Optional[str] = Field(default=None, description="Last name")
    skills: List[str] = Field(default_factory=list, description="Full replacement skill list")
    preferred_domain: Optional[str] = Field(default=None, description="e.g. 'web development'")
    preferred_location: Optional[str] = Field(default=None, description="Preferred location, or 'Remote'")
    university: Optional[str] = Field(default=None, description="University or institution name")
    field_of_study: Optional[str] = Field(default=None, description="e.g. 'Computer Science'")
    domain_interests: List[str] = Field(default_factory=list, description="List of domain interests")


class StudentResponse(BaseModel):
    """What the API returns for a student - never includes password_hash."""
    id: str
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: EmailStr
    skills: List[str]
    preferred_domain: Optional[str] = None
    preferred_location: Optional[str] = None
    university: Optional[str] = None
    field_of_study: Optional[str] = None
    domain_interests: List[str] = Field(default_factory=list)
    created_at: datetime


class NotificationResponse(BaseModel):
    """Notification item derived from scrapers and matching engine."""
    id: str = Field(..., description="Unique notification ID")
    type: str = Field(..., description="'match', 'deadline', 'scraper', 'skill_gap', 'near_miss'")
    title: str = Field(..., description="Notification headline")
    timestamp: datetime = Field(..., description="Notification event timestamp")
    icon: str = Field(..., description="'sparkles', 'clock', 'bell', 'lightbulb'")
    read: bool = Field(default=False, description="Whether notification is read")
    link: Optional[str] = Field(default=None, description="Optional link to target listing or filter")
    source: Optional[str] = Field(default=None, description="Source scraper name")
    domain: Optional[str] = Field(default=None, description="Domain tag")

