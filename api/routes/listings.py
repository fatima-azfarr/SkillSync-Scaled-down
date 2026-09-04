"""
SkillSync - Listings API Routes

Endpoints:
    GET /listings          — List all listings with filters and pagination
    GET /listings/{id}     — Get a single listing by its ID

These are the core API endpoints that expose the scraped data.
The future React dashboard (FYP-I) will consume these endpoints.
"""

import math
from fastapi import APIRouter, Query, HTTPException
from bson import ObjectId
from typing import Optional

from api.database import get_database
from api.models import ListingResponse, PaginatedResponse
from api.config import config

# Create a router — this groups related endpoints together
# All routes in this file will be prefixed with nothing (added in main.py)
router = APIRouter(tags=["Listings"])


@router.get("/listings", response_model=PaginatedResponse,
            summary="List all listings",
            description="Get a paginated list of listings with optional filters.")
async def get_listings(
    source: Optional[str] = Query(None, description="Filter by source (e.g., 'rozee', 'devpost')"),
    keyword: Optional[str] = Query(None, description="Search in title and description"),
    domain: Optional[str] = Query(None, description="Filter by domain tag (FYP-I feature)"),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
):
    """
    List listings with optional filtering and pagination.
    
    Query parameters:
    - **source**: Filter by platform (rozee, mustakbil, internee, remotive, devpost, wuzzuf)
    - **keyword**: Search keyword in title and description
    - **domain**: Filter by domain tag (populated in FYP-I)
    - **page**: Page number for pagination
    - **page_size**: Number of results per page (default 20, max 100)
    
    Returns:
        Paginated list of listings with metadata
    """
    db = get_database()
    collection = db[config.LISTINGS_COLLECTION]
    
    # Build the MongoDB query filter
    # Only add conditions that the user actually provided
    query_filter = {}
    
    if source:
        # Exact match on source platform
        query_filter["source"] = source.lower()
    
    if keyword:
        # Text search in title and description using MongoDB regex
        # $or means: match if keyword is in title OR description
        # $regex with $options:"i" means case-insensitive search
        query_filter["$or"] = [
            {"title": {"$regex": keyword, "$options": "i"}},
            {"description_raw": {"$regex": keyword, "$options": "i"}},
        ]
    
    if domain:
        query_filter["domain_tag"] = domain
    
    # Count total matching documents (for pagination metadata)
    total = await collection.count_documents(query_filter)
    
    # Calculate pagination
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    skip = (page - 1) * page_size  # How many documents to skip
    
    # Fetch the listings from MongoDB
    # Sort by scraped_at descending (newest first)
    cursor = collection.find(query_filter) \
                        .sort("scraped_at", -1) \
                        .skip(skip) \
                        .limit(page_size)
    
    # Convert MongoDB documents to our response format
    listings = []
    async for doc in cursor:
        listings.append(ListingResponse(
            id=str(doc["_id"]),  # Convert ObjectId to string
            title=doc.get("title", ""),
            source=doc.get("source", ""),
            source_url=doc.get("source_url", ""),
            description_raw=doc.get("description_raw", ""),
            company=doc.get("company"),
            location=doc.get("location"),
            posted_date=doc.get("posted_date"),
            deadline=doc.get("deadline"),
            domain_tag=doc.get("domain_tag"),
            skills=doc.get("skills", []),
            scraped_at=doc.get("scraped_at"),
            is_active=doc.get("is_active", True),
        ))
    
    return PaginatedResponse(
        listings=listings,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/listings/{listing_id}", response_model=ListingResponse,
            summary="Get a single listing",
            description="Get detailed information about a specific listing by its ID.")
async def get_listing_by_id(listing_id: str):
    """
    Get a single listing by its MongoDB ID.
    
    Args:
        listing_id: The listing's unique ID (MongoDB ObjectId as string)
    
    Returns:
        The listing details
    
    Raises:
        404 if listing not found or invalid ID
    """
    db = get_database()
    collection = db[config.LISTINGS_COLLECTION]
    
    # Validate that the ID is a valid MongoDB ObjectId
    try:
        object_id = ObjectId(listing_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Invalid listing ID format")
    
    # Find the listing in MongoDB
    doc = await collection.find_one({"_id": object_id})
    
    if not doc:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    return ListingResponse(
        id=str(doc["_id"]),
        title=doc.get("title", ""),
        source=doc.get("source", ""),
        source_url=doc.get("source_url", ""),
        description_raw=doc.get("description_raw", ""),
        company=doc.get("company"),
        location=doc.get("location"),
        posted_date=doc.get("posted_date"),
        deadline=doc.get("deadline"),
        domain_tag=doc.get("domain_tag"),
        skills=doc.get("skills", []),
        scraped_at=doc.get("scraped_at"),
        is_active=doc.get("is_active", True),
    )
