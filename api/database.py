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

        # Enforce unique student emails at the database level
        await _database[config.STUDENTS_COLLECTION].create_index("email", unique=True)

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