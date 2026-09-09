"""
SkillSync - API Endpoint Tests

Tests for all 5 API endpoints:
    GET /                  — Root welcome message
    GET /listings          — Paginated listing list with filters
    GET /listings/{id}     — Single listing by ID
    GET /sources           — Scraper source information
    GET /health            — Health check
    GET /scrape/status     — Scraper run status

These tests use an in-process FastAPI test client (no real server needed).
They require a running MongoDB instance.
"""

import pytest
from datetime import datetime
from pymongo import MongoClient
import os

# Test database settings
TEST_MONGO_URI = os.getenv("TEST_MONGO_URI", "mongodb://localhost:27017")
TEST_DB_NAME = "skillsync_test"


def _seed_test_data():
    """Insert some test listings directly into MongoDB for API tests."""
    client = MongoClient(TEST_MONGO_URI)
    db = client[TEST_DB_NAME]
    
    test_listings = [
        {
            "title": "Python Developer Intern",
            "source": "rozee",
            "source_url": "https://rozee.pk/job/1",
            "description_raw": "Looking for Python interns with Django experience.",
            "company": "TechCo",
            "location": "Lahore",
            "posted_date": None,
            "deadline": None,
            "domain_tag": None,
            "skills": [],
            "scraped_at": datetime(2024, 1, 15, 10, 0, 0),
            "is_active": True,
            "fingerprint": "abc123unique1",
        },
        {
            "title": "Frontend Developer",
            "source": "wuzzuf",
            "source_url": "https://wuzzuf.net/job/2",
            "description_raw": "React.js frontend developer needed.",
            "company": "WebInc",
            "location": "Remote",
            "posted_date": None,
            "deadline": None,
            "domain_tag": None,
            "skills": [],
            "scraped_at": datetime(2024, 1, 15, 11, 0, 0),
            "is_active": True,
            "fingerprint": "abc123unique2",
        },
        {
            "title": "Data Science Hackathon",
            "source": "devpost",
            "source_url": "https://devpost.com/hackathon/3",
            "description_raw": "48-hour data science challenge.",
            "company": "HackOrg",
            "location": "Online",
            "posted_date": None,
            "deadline": None,
            "domain_tag": None,
            "skills": [],
            "scraped_at": datetime(2024, 1, 15, 12, 0, 0),
            "is_active": True,
            "fingerprint": "abc123unique3",
        },
    ]
    
    # Create unique index (same as the real pipeline does)
    db.listings.create_index("fingerprint", unique=True)
    db.listings.insert_many(test_listings)
    
    # Also insert a scraper run log
    db.scraper_runs.insert_one({
        "scraper_name": "rozee",
        "started_at": datetime(2024, 1, 15, 10, 0, 0),
        "finished_at": datetime(2024, 1, 15, 10, 5, 0),
        "listings_found": 10,
        "listings_new": 5,
        "listings_failed": 0,
        "status": "success",
        "errors": [],
    })
    
    client.close()


@pytest.fixture(autouse=True)
def seed_data():
    """Seed test data before each test and clean up after."""
    # Clean up any existing test data
    client = MongoClient(TEST_MONGO_URI)
    client.drop_database(TEST_DB_NAME)
    client.close()
    
    # Seed fresh test data
    _seed_test_data()
    
    yield
    
    # Clean up after test
    client = MongoClient(TEST_MONGO_URI)
    client.drop_database(TEST_DB_NAME)
    client.close()


@pytest.mark.asyncio
class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    async def test_root_returns_welcome(self, async_client):
        """GET / should return a welcome message."""
        response = await async_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "SkillSync" in data["message"]


@pytest.mark.asyncio
class TestListingsEndpoint:
    """Tests for the /listings endpoint."""
    
    async def test_get_all_listings(self, async_client):
        """GET /listings should return all listings."""
        response = await async_client.get("/listings")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["listings"]) == 3
    
    async def test_filter_by_source(self, async_client):
        """GET /listings?source=rozee should only return Rozee listings."""
        response = await async_client.get("/listings?source=rozee")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["listings"][0]["source"] == "rozee"
    
    async def test_filter_by_keyword(self, async_client):
        """GET /listings?keyword=Python should match title/description."""
        response = await async_client.get("/listings?keyword=Python")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        # All results should contain "Python" in title or description
        for listing in data["listings"]:
            has_keyword = (
                "python" in listing["title"].lower() or 
                "python" in listing["description_raw"].lower()
            )
            assert has_keyword
    
    async def test_pagination(self, async_client):
        """Pagination should limit results per page."""
        response = await async_client.get("/listings?page=1&page_size=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["listings"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total_pages"] == 2  # 3 total / 2 per page = 2 pages
    
    async def test_pagination_page_2(self, async_client):
        """Page 2 should return remaining listings."""
        response = await async_client.get("/listings?page=2&page_size=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["listings"]) == 1  # Only 1 remaining on page 2
    
    async def test_pagination_metadata(self, async_client):
        """Pagination response should include correct metadata."""
        response = await async_client.get("/listings?page_size=10")
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data


@pytest.mark.asyncio
class TestListingByIdEndpoint:
    """Tests for the /listings/{id} endpoint."""
    
    async def test_get_listing_by_valid_id(self, async_client):
        """GET /listings/{id} with a valid ID should return the listing."""
        # First get all listings to find a valid ID
        response = await async_client.get("/listings")
        listings = response.json()["listings"]
        listing_id = listings[0]["id"]
        
        # Now fetch by ID
        response = await async_client.get(f"/listings/{listing_id}")
        
        assert response.status_code == 200
        assert response.json()["id"] == listing_id
    
    async def test_invalid_id_returns_404(self, async_client):
        """GET /listings/{id} with an invalid ID should return 404."""
        response = await async_client.get("/listings/invalid-id-format")
        
        assert response.status_code == 404
    
    async def test_nonexistent_id_returns_404(self, async_client):
        """GET /listings/{id} with a valid but nonexistent ID should return 404."""
        # Valid ObjectId format but doesn't exist in DB
        response = await async_client.get("/listings/507f1f77bcf86cd799439011")
        
        assert response.status_code == 404


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Tests for the /health endpoint."""
    
    async def test_health_check(self, async_client):
        """GET /health should return ok status."""
        response = await async_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "connected"


@pytest.mark.asyncio
class TestSourcesEndpoint:
    """Tests for the /sources endpoint."""
    
    async def test_get_sources(self, async_client):
        """GET /sources should return source information."""
        response = await async_client.get("/sources")
        
        assert response.status_code == 200
        sources = response.json()
        assert len(sources) >= 1
        
        # Each source should have name, total_listings, last_scraped
        for source in sources:
            assert "name" in source
            assert "total_listings" in source


@pytest.mark.asyncio
class TestScrapeStatusEndpoint:
    """Tests for the /scrape/status endpoint."""
    
    async def test_get_scrape_status(self, async_client):
        """GET /scrape/status should return scraper run info."""
        response = await async_client.get("/scrape/status")
        
        assert response.status_code == 200
        statuses = response.json()
        assert len(statuses) >= 1
        
        # Check the rozee scraper status
        rozee_status = next((s for s in statuses if s["scraper_name"] == "rozee"), None)
        assert rozee_status is not None
        assert rozee_status["status"] == "success"
        assert rozee_status["listings_found"] == 10


@pytest.mark.asyncio
class TestNotificationsEndpoint:
    """Tests for the /notifications endpoint."""
    
    async def test_get_notifications(self, async_client):
        """GET /notifications should return scraper-derived notifications."""
        response = await async_client.get("/notifications")
        
        assert response.status_code == 200
        notifications = response.json()
        assert isinstance(notifications, list)
        assert len(notifications) >= 1
        
        # Each notification should have required fields
        for item in notifications:
            assert "id" in item
            assert "type" in item
            assert "title" in item
            assert "icon" in item
            assert "timestamp" in item
            assert "read" in item


