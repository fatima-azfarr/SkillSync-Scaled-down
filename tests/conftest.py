"""
SkillSync - Test Configuration (Shared Fixtures)

pytest fixtures are reusable setup/teardown functions for tests.
This file is automatically discovered by pytest and its fixtures
are available to all test files.

We use a separate test database so tests don't affect real data.
"""

import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from httpx import AsyncClient, ASGITransport
import os

# Use test database to avoid touching real data
TEST_MONGO_URI = os.getenv("TEST_MONGO_URI", "mongodb://localhost:27017")
TEST_DB_NAME = "skillsync_test"


@pytest.fixture
def sample_listing():
    """
    A sample listing dictionary, as a scraper would produce it.
    Used as test input for the pipeline and model tests.
    """
    return {
        "title": "Software Engineering Intern",
        "source_url": "https://example.com/job/123",
        "description_raw": "Looking for a Python developer intern for 3 months.",
        "company": "TechCorp",
        "location": "Lahore, Pakistan",
        "posted_date": None,
        "deadline": None,
    }


@pytest.fixture
def sample_listing_2():
    """A second sample listing (different from the first) for dedup testing."""
    return {
        "title": "Data Science Internship",
        "source_url": "https://example.com/job/456",
        "description_raw": "Join our data team. ML experience preferred.",
        "company": "DataInc",
        "location": "Remote",
        "posted_date": None,
        "deadline": None,
    }


@pytest.fixture
def mongo_client():
    """
    Create a synchronous MongoDB client for pipeline/integration tests.
    Cleans up the test database after each test.
    """
    client = MongoClient(TEST_MONGO_URI)
    db = client[TEST_DB_NAME]
    
    yield client
    
    # Cleanup: drop the test database after each test
    client.drop_database(TEST_DB_NAME)
    client.close()


@pytest_asyncio.fixture
async def async_client():
    """
    Create an async HTTP test client for API tests.
    
    This client sends requests directly to the FastAPI app
    without needing a running server (in-process testing).
    """
    # Set environment variables for the test database
    os.environ["MONGO_URI"] = TEST_MONGO_URI
    os.environ["DATABASE_NAME"] = TEST_DB_NAME
    
    # Import app after setting env vars
    from api.main import app
    from api.database import connect_to_mongodb, close_mongodb_connection
    
    # Connect to test database
    await connect_to_mongodb()
    
    # Create async test client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    
    # Cleanup: drop test database and close connection
    motor_client = AsyncIOMotorClient(TEST_MONGO_URI)
    await motor_client.drop_database(TEST_DB_NAME)
    motor_client.close()
    
    await close_mongodb_connection()
