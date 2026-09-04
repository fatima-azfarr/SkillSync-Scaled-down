"""
SkillSync - Shared Data Processing Pipeline

This is the heart of the data flow. Every scraper feeds its raw listings
into this pipeline, which processes them through 4 steps:

    Raw Listings → Clean → Fingerprint → Deduplicate → Validate → Save to MongoDB

The pipeline ensures:
1. All data is cleaned (whitespace, encoding issues)
2. Each listing gets a unique SHA-256 fingerprint
3. Duplicates are detected and skipped (not stored twice)
4. Only valid data (passes Pydantic schema) gets saved
5. Run statistics are logged for monitoring
"""

from datetime import datetime
from typing import List, Dict, Any
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from scrapers.models import ListingSchema, ScraperRunLog
from scrapers.fingerprint import generate_fingerprint
from scrapers.utils import clean_text
from scrapers.logger import get_logger, log_scraper_end
from scrapers.config import config

logger = get_logger("pipeline")


class Pipeline:
    """
    Shared processing pipeline for all scrapers.
    
    Usage:
        pipeline = Pipeline()
        pipeline.connect()
        stats = pipeline.process_listings(raw_listings, scraper_name="rozee")
        pipeline.close()
    """
    
    def __init__(self):
        """Initialize pipeline (call connect() before processing)."""
        self.client = None
        self.db = None
        self.listings_collection = None
        self.runs_collection = None
    
    def connect(self):
        """
        Connect to MongoDB.
        
        Creates the database and collections if they don't exist.
        Sets up a unique index on 'fingerprint' to enforce deduplication
        at the database level.
        """
        logger.info(f"Connecting to MongoDB at {config.MONGO_URI}")
        self.client = MongoClient(config.MONGO_URI)
        self.db = self.client[config.DATABASE_NAME]
        self.listings_collection = self.db[config.LISTINGS_COLLECTION]
        self.runs_collection = self.db[config.SCRAPER_RUNS_COLLECTION]
        
        # Create unique index on fingerprint - this is the dedup key
        # If we try to insert a listing with an existing fingerprint,
        # MongoDB will reject it (DuplicateKeyError)
        self.listings_collection.create_index("fingerprint", unique=True)
        
        # Compound index for filtered queries (source + scraped_at)
        # This makes API queries like "get all rozee listings" fast
        self.listings_collection.create_index([("source", 1), ("scraped_at", -1)])
        
        logger.info("Connected to MongoDB and indexes created")
    
    def close(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    def process_listings(self, raw_listings: List[Dict[str, Any]], 
                         scraper_name: str) -> Dict[str, int]:
        """
        Process a batch of raw listings through the full pipeline.
        
        Steps:
        1. Clean text fields
        2. Generate SHA-256 fingerprint
        3. Validate with Pydantic schema
        4. Insert into MongoDB (duplicates auto-rejected by unique index)
        
        Args:
            raw_listings: List of dictionaries from a scraper
            scraper_name: Name of the scraper (for logging)
            
        Returns:
            Dictionary with processing statistics:
            {
                "found": total raw listings,
                "new": successfully inserted (non-duplicate),
                "failed": validation or insert errors
            }
        """
        stats = {"found": len(raw_listings), "new": 0, "failed": 0}
        errors = []
        
        # Create a run log entry
        run_log = ScraperRunLog(
            scraper_name=scraper_name,
            listings_found=len(raw_listings),
            status="running"
        )
        
        logger.info(f"Processing {len(raw_listings)} listings from {scraper_name}")
        
        for raw in raw_listings:
            try:
                # Step 1: Clean text fields
                cleaned = self._clean_listing(raw, scraper_name)
                
                # Step 2: Generate fingerprint
                cleaned["fingerprint"] = generate_fingerprint(
                    title=cleaned.get("title", ""),
                    source=cleaned.get("source", ""),
                    source_url=cleaned.get("source_url", "")
                )
                
                # Step 3: Validate with Pydantic
                listing = ListingSchema(**cleaned)
                
                # Step 4: Insert into MongoDB
                # Convert Pydantic model to dictionary for MongoDB
                listing_dict = listing.model_dump()
                
                try:
                    self.listings_collection.insert_one(listing_dict)
                    stats["new"] += 1
                except DuplicateKeyError:
                    # This listing already exists (same fingerprint)
                    # This is normal and expected - not an error
                    pass
                    
            except Exception as e:
                stats["failed"] += 1
                error_msg = f"Failed to process listing: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
        
        # Update and save the run log
        run_log.finished_at = datetime.utcnow()
        run_log.listings_new = stats["new"]
        run_log.listings_failed = stats["failed"]
        run_log.errors = errors
        run_log.status = "success" if stats["failed"] == 0 else "partial"
        
        self.runs_collection.insert_one(run_log.model_dump())
        
        # Log summary
        log_scraper_end(logger, scraper_name, stats["found"], stats["new"], stats["failed"])
        
        return stats
    
    def _clean_listing(self, raw: Dict[str, Any], source: str) -> Dict[str, Any]:
        """
        Clean a raw listing dictionary.
        
        - Cleans text fields (whitespace, encoding)
        - Ensures the source field is set
        - Adds scraped_at timestamp
        
        Args:
            raw: Raw listing dictionary from scraper
            source: Source platform name
            
        Returns:
            Cleaned listing dictionary
        """
        cleaned = {}
        
        # Clean text fields
        cleaned["title"] = clean_text(raw.get("title", ""))
        cleaned["source"] = source
        cleaned["source_url"] = raw.get("source_url", "").strip()
        cleaned["description_raw"] = clean_text(raw.get("description_raw", ""))
        cleaned["company"] = clean_text(raw.get("company", "")) or None
        cleaned["location"] = clean_text(raw.get("location", "")) or None
        
        # Copy date fields as-is (scrapers handle date parsing)
        cleaned["posted_date"] = raw.get("posted_date")
        cleaned["deadline"] = raw.get("deadline")
        
        # Set metadata
        cleaned["scraped_at"] = datetime.utcnow()
        cleaned["is_active"] = True
        
        # Phase 2 fields - empty for now
        cleaned["domain_tag"] = None
        cleaned["skills"] = []
        
        return cleaned
