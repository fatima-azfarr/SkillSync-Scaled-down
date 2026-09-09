"""
SkillSync - Pipeline Integration Tests

These tests verify the full pipeline flow:
    Raw listings → clean → fingerprint → dedupe → validate → save to MongoDB

Unlike unit tests (which test one function in isolation),
integration tests verify that multiple components work together correctly.

NOTE: These tests require a running MongoDB instance.
"""

import pytest
from scrapers.pipeline import Pipeline
from scrapers.config import config

# Use test database
TEST_DB_NAME = "skillsync_test"


class TestPipeline:
    """Integration tests for the data processing pipeline."""
    
    @pytest.fixture(autouse=True)
    def setup_pipeline(self, mongo_client):
        """
        Set up a pipeline with test database before each test.
        Clean up after each test.
        """
        # Override config to use test database
        original_db = config.DATABASE_NAME
        config.DATABASE_NAME = TEST_DB_NAME
        
        self.pipeline = Pipeline()
        self.pipeline.connect()
        self.mongo_client = mongo_client
        
        yield
        
        self.pipeline.close()
        config.DATABASE_NAME = original_db
    
    def test_process_single_listing(self, sample_listing):
        """A single valid listing should be processed and saved."""
        raw_listings = [sample_listing]
        
        stats = self.pipeline.process_listings(raw_listings, "test_source")
        
        assert stats["found"] == 1
        assert stats["new"] == 1
        assert stats["failed"] == 0
    
    def test_process_multiple_listings(self, sample_listing, sample_listing_2):
        """Multiple different listings should all be saved."""
        raw_listings = [sample_listing, sample_listing_2]
        
        stats = self.pipeline.process_listings(raw_listings, "test_source")
        
        assert stats["found"] == 2
        assert stats["new"] == 2
        assert stats["failed"] == 0
    
    def test_duplicate_detection(self, sample_listing):
        """
        Processing the same listing twice should detect the duplicate.
        The first run inserts it; the second run skips it.
        """
        raw_listings = [sample_listing]
        
        # First run — listing should be inserted
        stats1 = self.pipeline.process_listings(raw_listings, "test_source")
        assert stats1["new"] == 1
        
        # Second run — same listing should be detected as duplicate
        stats2 = self.pipeline.process_listings(raw_listings, "test_source")
        assert stats2["new"] == 0  # Not inserted again
    
    def test_invalid_listing_rejected(self):
        """A listing with missing required fields should be rejected."""
        # Missing 'title' which is required
        invalid_listings = [
            {
                "source_url": "https://example.com/job/123",
                "description_raw": "Some description",
            }
        ]
        
        stats = self.pipeline.process_listings(invalid_listings, "test_source")
        
        assert stats["found"] == 1
        assert stats["new"] == 0
        assert stats["failed"] == 1  # Should fail validation
    
    def test_empty_listing_batch(self):
        """Processing an empty batch should return zero stats."""
        stats = self.pipeline.process_listings([], "test_source")
        
        assert stats["found"] == 0
        assert stats["new"] == 0
        assert stats["failed"] == 0
    
    def test_scraper_run_logged(self, sample_listing):
        """Each pipeline run should create a log entry in scraper_runs."""
        raw_listings = [sample_listing]
        
        self.pipeline.process_listings(raw_listings, "test_source")
        
        # Check that a run log was created
        db = self.mongo_client[TEST_DB_NAME]
        run_logs = list(db[config.SCRAPER_RUNS_COLLECTION].find(
            {"scraper_name": "test_source"}
        ))
        
        assert len(run_logs) == 1
        assert run_logs[0]["listings_found"] == 1
        assert run_logs[0]["listings_new"] == 1
    
    def test_listing_stored_correctly(self, sample_listing):
        """Saved listings should have all expected fields."""
        self.pipeline.process_listings([sample_listing], "test_source")
        
        # Fetch the listing from MongoDB
        db = self.mongo_client[TEST_DB_NAME]
        listing = db[config.LISTINGS_COLLECTION].find_one()
        
        assert listing is not None
        assert listing["title"] == "Software Engineering Intern"
        assert listing["source"] == "test_source"
        assert listing["fingerprint"] != ""  # Should have a fingerprint
        assert listing["is_active"] is True
        assert isinstance(listing["skills"], list)
        assert "python" in listing["skills"]
