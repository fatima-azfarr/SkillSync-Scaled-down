"""
SkillSync - Database Connection (Motor - Async MongoDB)

Motor is the async driver for MongoDB. It works with FastAPI's
async/await pattern, meaning the API can handle multiple requests
simultaneously without blocking on database operations.

Why Motor instead of PyMongo?
- PyMongo is synchronous (blocks while waiting for DB)
- Motor is asynchronous (can serve other requests while waiting)
- FastAPI is async by design, so Motor is the natural fit

Usage:
    # In FastAPI startup:
    await connect_to_mongodb()
    
    # In route handlers:
    from api.database import get_database
    db = get_database()
    listings = await db.listings.find({}).to_list(20)
"""

from motor.motor_asyncio import AsyncIOMotorClient
from api.config import config

# Global database client and database references
# These are set when the app starts and used throughout the API
_client: AsyncIOMotorClient = None
_database = None


async def connect_to_mongodb():
    """
    Connect to MongoDB using Motor (async driver).
    Called once when the FastAPI app starts up.
    """
    global _client, _database
    
    print(f"[DATABASE] Connecting to MongoDB at {config.MONGO_URI}...")
    _client = AsyncIOMotorClient(config.MONGO_URI)
    _database = _client[config.DATABASE_NAME]
    
    # Test the connection
    try:
        await _client.admin.command("ping")
        print("[DATABASE] Connected to MongoDB successfully!")
    except Exception as e:
        print(f"[DATABASE] Failed to connect to MongoDB: {e}")
        raise


async def close_mongodb_connection():
    """
    Close the MongoDB connection.
    Called when the FastAPI app shuts down.
    """
    global _client
    
    if _client:
        _client.close()
        print("[DATABASE] MongoDB connection closed.")


def get_database():
    """
    Get the database instance for use in route handlers.
    
    Returns:
        Motor async database instance
    
    Usage in a route:
        db = get_database()
        result = await db.listings.find_one({"_id": some_id})
    """
    return _database
