"""
SkillSync - Sources API Route

Endpoint:
    GET /sources — List all active scraper sources with their last run time

This endpoint is useful for:
- Seeing which platforms we're scraping
- Checking when each source was last scraped
- Quick overview of data distribution across sources
"""

from fastapi import APIRouter
from typing import List

from api.database import get_database
from api.models import SourceInfo
from api.config import config

router = APIRouter(tags=["Sources"])


@router.get("/sources", response_model=List[SourceInfo],
            summary="List scraper sources",
            description="Get a list of all scraper sources with listing counts and last scrape times.")
async def get_sources():
    """
    Get information about each scraper source.
    
    Uses MongoDB aggregation to:
    1. Group listings by source
    2. Count how many listings each source has
    3. Find the most recent scraped_at timestamp per source
    
    Returns:
        List of source information objects
    """
    db = get_database()
    collection = db[config.LISTINGS_COLLECTION]
    
    # MongoDB Aggregation Pipeline
    # This is like a SQL GROUP BY — it groups documents by 'source'
    # and computes counts and max timestamps per group
    pipeline = [
        {
            # Group by the 'source' field
            "$group": {
                "_id": "$source",  # Group key
                "total_listings": {"$sum": 1},  # Count documents in each group
                "last_scraped": {"$max": "$scraped_at"},  # Most recent scrape time
            }
        },
        {
            # Sort alphabetically by source name
            "$sort": {"_id": 1}
        }
    ]
    
    sources = []
    async for doc in collection.aggregate(pipeline):
        sources.append(SourceInfo(
            name=doc["_id"],
            total_listings=doc["total_listings"],
            last_scraped=doc.get("last_scraped"),
        ))
    
    return sources
