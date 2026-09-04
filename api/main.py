"""
SkillSync - FastAPI Application (Main Entry Point)

This is the main file for the API service. It:
1. Creates the FastAPI application
2. Registers all route handlers
3. Connects to MongoDB on startup
4. Disconnects from MongoDB on shutdown
5. Adds CORS middleware (for future React frontend)
6. Auto-generates Swagger/OpenAPI documentation at /docs

Usage:
    uvicorn api.main:app --reload
    
Or via Docker:
    docker-compose up api
    
Then visit: http://localhost:8000/docs for Swagger UI
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.database import connect_to_mongodb, close_mongodb_connection
from api.routes import listings, sources, health


# Lifespan context manager handles startup and shutdown events
# This replaces the older @app.on_event("startup") pattern
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the application lifecycle.
    
    - On startup: connect to MongoDB
    - On shutdown: close the MongoDB connection
    """
    # STARTUP: Connect to MongoDB
    await connect_to_mongodb()
    
    yield  # The app runs between startup and shutdown
    
    # SHUTDOWN: Close MongoDB connection
    await close_mongodb_connection()


# Create the FastAPI application
app = FastAPI(
    title="SkillSync API",
    description=(
        "AI-Driven Internship & Tech Event Discovery Platform.\n\n"
        "Phase 1 API — exposes scraped listings from 6 platforms:\n"
        "Rozee.pk, Mustakbil.com, Internee.pk, Remotive, Devpost, Wuzzuf.net\n\n"
        "**Endpoints:**\n"
        "- `GET /listings` — Browse listings with filters and pagination\n"
        "- `GET /listings/{id}` — Get a specific listing\n"
        "- `GET /sources` — View scraper sources and stats\n"
        "- `GET /health` — API health check\n"
        "- `GET /scrape/status` — Scraper run status"
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
# This allows the future React frontend (FYP-I) to make requests to this API
# For now, we allow all origins since there's no sensitive user data
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Allow all origins (restrict in production)
    allow_credentials=True,
    allow_methods=["*"],       # Allow all HTTP methods
    allow_headers=["*"],       # Allow all headers
)

# Register route handlers
# Each router handles a group of related endpoints
app.include_router(listings.router)   # /listings, /listings/{id}
app.include_router(sources.router)    # /sources
app.include_router(health.router)     # /health, /scrape/status


# Root endpoint — a simple welcome message
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint. Returns a welcome message and links to docs.
    """
    return {
        "message": "Welcome to SkillSync API",
        "version": "0.1.0",
        "docs": "/docs",
        "description": "AI-Driven Internship & Tech Event Discovery Platform",
    }
