"""
SkillSync - Health & Scraper Status Routes

Endpoints:
    GET /health         — Liveness check (is the API running?)
    GET /scrape/status  — Last run summary for each scraper

The /health endpoint is also used by Docker's healthcheck to monitor
whether the API container is alive and can reach MongoDB.
"""

from fastapi import APIRouter
from typing import List
from datetime import datetime

from api.database import get_database
from api.models import HealthResponse, ScrapeStatusResponse
from api.config import config

router = APIRouter(tags=["Health & Status"])


@router.get("/health", response_model=HealthResponse,
            summary="Health check",
            description="Check if the API is running and can connect to MongoDB.")
async def health_check():
    """
    Simple health check endpoint.
    
    Returns the API status and database connectivity.
    Used by Docker healthcheck to monitor container health.
    
    Returns:
        {"status": "ok", "database": "connected", "timestamp": "..."}
    """
    db = get_database()
    
    # Check if we can reach MongoDB
    try:
        # A simple 'ping' command to test the connection
        await db.command("ping")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        database=db_status,
        timestamp=datetime.utcnow(),
    )


@router.get("/scrape/status", response_model=List[ScrapeStatusResponse],
            summary="Scraper run status",
            description="Get the last run summary for each scraper source.")
async def get_scrape_status():
    """
    Get the status of the most recent run for each scraper.
    
    This is useful for debugging:
    - When did each scraper last run?
    - How many listings did it find?
    - Did any errors occur?
    
    Returns:
        List of scraper status objects (one per source)
    """
    db = get_database()
    runs_collection = db[config.SCRAPER_RUNS_COLLECTION]
    
    # Get the most recent run for each scraper using MongoDB aggregation
    pipeline = [
        # Sort by started_at descending (most recent first)
        {"$sort": {"started_at": -1}},
        # Group by scraper name and take the first (most recent) document
        {
            "$group": {
                "_id": "$scraper_name",
                "started_at": {"$first": "$started_at"},
                "finished_at": {"$first": "$finished_at"},
                "listings_found": {"$first": "$listings_found"},
                "listings_new": {"$first": "$listings_new"},
                "listings_failed": {"$first": "$listings_failed"},
                "status": {"$first": "$status"},
                "errors": {"$first": "$errors"},
            }
        },
        # Sort by scraper name alphabetically
        {"$sort": {"_id": 1}},
    ]
    
    statuses = []
    async for doc in runs_collection.aggregate(pipeline):
        statuses.append(ScrapeStatusResponse(
            scraper_name=doc["_id"],
            started_at=doc.get("started_at"),
            finished_at=doc.get("finished_at"),
            listings_found=doc.get("listings_found", 0),
            listings_new=doc.get("listings_new", 0),
            listings_failed=doc.get("listings_failed", 0),
            status=doc.get("status", "unknown"),
            errors=doc.get("errors", []),
        ))
    
    return statuses
