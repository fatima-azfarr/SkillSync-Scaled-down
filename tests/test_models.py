"""
SkillSync - Pydantic Model Unit Tests

Tests for the ListingSchema Pydantic model.
These ensure that:
1. Valid listings pass validation
2. Invalid/missing required fields are rejected
3. Optional fields can be None without errors
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from scrapers.models import ListingSchema, ScraperRunLog


class TestListingSchema:
    """Unit tests for the ListingSchema Pydantic model."""
    
    def test_valid_listing(self, sample_listing):
        """A listing with all required fields should pass validation."""
        listing = ListingSchema(
            title=sample_listing["title"],
            source="rozee",
            source_url=sample_listing["source_url"],
            description_raw=sample_listing["description_raw"],
        )
        
        assert listing.title == "Software Engineering Intern"
        assert listing.source == "rozee"
        assert listing.is_active is True  # Default value
    
    def test_valid_listing_with_all_fields(self, sample_listing):
        """A listing with all fields (including optional) should pass."""
        listing = ListingSchema(
            title=sample_listing["title"],
            source="rozee",
            source_url=sample_listing["source_url"],
            description_raw=sample_listing["description_raw"],
            company=sample_listing["company"],
            location=sample_listing["location"],
            posted_date=datetime(2024, 1, 15),
            deadline=datetime(2024, 2, 15),
            domain_tag="software_engineering",
            skills=["python", "django"],
        )
        
        assert listing.company == "TechCorp"
        assert listing.skills == ["python", "django"]
    
    def test_missing_title_rejected(self):
        """A listing without a title should fail validation."""
        with pytest.raises(ValidationError):
            ListingSchema(
                # title is missing!
                source="rozee",
                source_url="https://example.com/job/123",
            )
    
    def test_missing_source_rejected(self):
        """A listing without a source should fail validation."""
        with pytest.raises(ValidationError):
            ListingSchema(
                title="Python Intern",
                # source is missing!
                source_url="https://example.com/job/123",
            )
    
    def test_missing_source_url_rejected(self):
        """A listing without a source_url should fail validation."""
        with pytest.raises(ValidationError):
            ListingSchema(
                title="Python Intern",
                source="rozee",
                # source_url is missing!
            )
    
    def test_optional_fields_can_be_none(self):
        """Optional fields should default to None without errors."""
        listing = ListingSchema(
            title="Python Intern",
            source="rozee",
            source_url="https://example.com",
        )
        
        assert listing.posted_date is None
        assert listing.deadline is None
        assert listing.location is None
        assert listing.company is None
        assert listing.domain_tag is None
    
    def test_skills_defaults_to_empty_list(self):
        """Skills should default to an empty list (populated in FYP-I)."""
        listing = ListingSchema(
            title="Python Intern",
            source="rozee",
            source_url="https://example.com",
        )
        
        assert listing.skills == []
    
    def test_scraped_at_auto_set(self):
        """scraped_at should be automatically set to current time."""
        listing = ListingSchema(
            title="Python Intern",
            source="rozee",
            source_url="https://example.com",
        )
        
        assert listing.scraped_at is not None
        assert isinstance(listing.scraped_at, datetime)
    
    def test_description_defaults_to_empty(self):
        """description_raw should default to empty string."""
        listing = ListingSchema(
            title="Python Intern",
            source="rozee",
            source_url="https://example.com",
        )
        
        assert listing.description_raw == ""


class TestScraperRunLog:
    """Unit tests for the ScraperRunLog model."""
    
    def test_valid_run_log(self):
        """A valid run log should pass validation."""
        log = ScraperRunLog(
            scraper_name="rozee",
            listings_found=50,
            listings_new=10,
            status="success",
        )
        
        assert log.scraper_name == "rozee"
        assert log.listings_found == 50
        assert log.errors == []  # Default empty list
    
    def test_run_log_with_errors(self):
        """A run log with errors should store them properly."""
        log = ScraperRunLog(
            scraper_name="mustakbil",
            listings_found=0,
            status="failed",
            errors=["Connection timeout", "Parse error on card 5"],
        )
        
        assert len(log.errors) == 2
        assert log.status == "failed"
