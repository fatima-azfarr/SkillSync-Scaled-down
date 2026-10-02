from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import config
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

# Add CORS middleware with strict origin policies
# Wildcards with credentials are systematically rejected by browsers and insecure
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOWED_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)

# Defensive Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    return response


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