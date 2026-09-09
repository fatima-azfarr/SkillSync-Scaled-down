from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.database import close_mongodb_connection, connect_to_mongodb
from api.routes import health, listings, notifications, sources, students


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
        "- `GET /scrape/status` — Scraper run status\n"
        "- `POST /students/register` — Register a new student\n"
        "- `POST /students/login` — Log in a student\n"
        "- `GET /students/{id}` — Get a student's profile\n"
        "- `PUT /students/{id}/profile` — Update a student's full profile\n"
        "- `PUT /students/{id}/skills` — Update a student's skill list\n"
        "- `PUT /students/{id}/preferences` — Update a student's preferences"
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
app.include_router(listings.router)        # /listings, /listings/{id}
app.include_router(sources.router)         # /sources
app.include_router(health.router)          # /health, /scrape/status
app.include_router(students.router)        # /students/register, /students/login, etc.
app.include_router(notifications.router)   # /notifications


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