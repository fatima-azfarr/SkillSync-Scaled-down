# SkillSync — AI-Driven Internship & Tech Event Discovery Platform

> Phase 1: Backend Data Pipeline — Scraping, Processing & API

## Overview

SkillSync aggregates internship and tech event listings from **6 platforms**, cleans and deduplicates them, stores them in MongoDB, and exposes them through a REST API.

### Data Sources
| Platform | Method | Type |
|---|---|---|
| Rozee.pk | Selenium | Internships (Pakistan) |
| Mustakbil.com | BeautifulSoup | Internships (Pakistan) |
| Internee.pk | Selenium | Internships (Pakistan) |
| Remotive | JSON API | Remote tech jobs |
| Devpost | Selenium | Hackathons & challenges |
| Wuzzuf.net | BeautifulSoup | Internships (Middle East) |

### Architecture

```
APScheduler (12-hour cycle)
         │
    ┌────┼────┬────┬────┬────┐
    ▼    ▼    ▼    ▼    ▼    ▼
 Rozee Mustakbil Internee Remotive Devpost Wuzzuf
    │    │    │    │    │    │
    └────┴────┴──┬─┴────┴────┘
                 ▼
    Shared Pipeline (clean → fingerprint → dedupe → validate)
                 ▼
             MongoDB
                 ▼
    FastAPI (REST API + Swagger docs)
```
---

## Quick Start (Docker)

**Prerequisites:** Docker and Docker Compose installed.

```bash
# 1. Clone the repository
git clone https://github.com/your-username/SkillSync.git
cd SkillSync

# 2. Create your .env file
cp .env.example .env

# 3. Start all services
docker-compose up

# 4. Open Swagger UI in your browser
# http://localhost:8000/docs
```

That's it! MongoDB, the API, and the scrapers all start automatically.


---

## Quick Start (Docker)

**Prerequisites:** Docker and Docker Compose installed.

```bash
# 1. Clone the repository
git clone https://github.com/your-username/SkillSync.git
cd SkillSync

# 2. Create your .env file
cp .env.example .env

# 3. Start all services
docker-compose up

# 4. Open Swagger UI in your browser
# http://localhost:8000/docs
```

That's it! MongoDB, the API, and the scrapers all start automatically.

---

## Quick Start (Local Development)

**Prerequisites:** Python 3.11 (newer versions like 3.13/3.14 currently fail to build `lxml` and `pydantic-core` — no compatible wheels yet), MongoDB installed locally, Google Chrome installed.

```bash
# 1. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate     # Mac/Linux
venv\Scripts\activate        # Windows

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Create your .env file
cp .env.example .env
# Edit .env with your MongoDB URI — for local MongoDB (not Docker), use:
# MONGODB_URI=mongodb://localhost:27017

# 4. Start MongoDB if it isn't already running
mongod --dbpath ~/data/db
# Leave this running in its own terminal

# 5. Start the API server (in a new terminal)
source venv/bin/activate
uvicorn api.main:app --reload
# Runs at http://127.0.0.1:8000

# 6. Start the scrapers (in a separate terminal)
source venv/bin/activate
python -m scrapers.main
# If Selenium scrapers (wuzzuf, rozee, internee, devpost) fail with a
# chromedriver "Exec format error", clear the driver cache and retry:
#   rm -rf ~/.wdm
#   python -m scrapers.main

# 7. Serve the frontend (in a separate terminal)
cd frontend
python3 -m http.server 5500
# Open http://localhost:5500 in your browser
```

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Welcome message |
| `/listings` | GET | List all listings (with filters & pagination) |
| `/listings/{id}` | GET | Get a single listing by ID |
| `/sources` | GET | List scraper sources with stats |
| `/health` | GET | Health check (API + database) |
| `/scrape/status` | GET | Last scraper run summary |

### Query Parameters for `/listings`

| Parameter | Type | Description | Example |
|---|---|---|---|
| `source` | string | Filter by platform | `?source=rozee` |
| `keyword` | string | Search in title/description | `?keyword=python` |
| `domain` | string | Filter by domain (FYP-I) | `?domain=web_dev` |
| `page` | int | Page number (default: 1) | `?page=2` |
| `page_size` | int | Results per page (default: 20, max: 100) | `?page_size=10` |

### Example API Calls

```bash
# Get all listings
curl http://localhost:8000/listings

# Filter by source
curl http://localhost:8000/listings?source=remotive

# Search for Python internships
curl http://localhost:8000/listings?keyword=python

# Paginate results
curl http://localhost:8000/listings?page=1&page_size=5

# Health check
curl http://localhost:8000/health
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MONGODB_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `DATABASE_NAME` | `skillsync` | MongoDB database name |
| `SCRAPE_INTERVAL_HOURS` | `12` | Hours between scrape cycles |
| `LOG_LEVEL` | `INFO` | Logging level |
| `HEADLESS` | `true` | Run Selenium in headless mode |
| `ROZEE_SESSION_COOKIE` | (empty) | Optional CAPTCHA bypass cookie |

---

## Project Structure

```
SkillSync/
├── api/                          # FastAPI REST API service
│   ├── Dockerfile
│   ├── main.py                   # App entry point
│   ├── config.py                 # Settings
│   ├── database.py               # MongoDB connection (Motor)
│   ├── models.py                 # Response models
│   └── routes/
│       ├── listings.py           # /listings endpoints
│       ├── sources.py            # /sources endpoint
│       └── health.py             # /health + /scrape/status
│
├── scrapers/                     # Scraper service
│   ├── Dockerfile
│   ├── main.py                   # Entry point + scheduler
│   ├── config.py                 # Settings
│   ├── pipeline.py               # Processing pipeline
│   ├── models.py                 # Pydantic schemas
│   ├── fingerprint.py            # SHA-256 dedup hashing
│   ├── logger.py                 # Structured logging
│   ├── utils.py                  # UA rotation, delays, Selenium
│   └── spiders/
│       ├── base.py               # Base scraper class
│       ├── rozee.py              # Rozee.pk (Selenium)
│       ├── mustakbil.py          # Mustakbil (BeautifulSoup)
│       ├── internee.py           # Internee.pk (Selenium)
│       ├── remotive.py           # Remotive (JSON API)
│       ├── devpost.py            # Devpost (Selenium)
│       └── wuzzuf.py             # Wuzzuf (BeautifulSoup)
│
├── tests/                        # Test suite
│   ├── conftest.py               # Shared fixtures
│   ├── test_fingerprint.py       # Unit: hashing
│   ├── test_models.py            # Unit: schema validation
│   ├── test_pipeline.py          # Integration: pipeline
│   └── test_api.py               # API: all endpoints
│
├── docker-compose.yml            # Full stack orchestration
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

---


---

## Running Tests

```bash
# Make sure MongoDB is running, then:
pytest tests/ -v

# Run specific test files
pytest tests/test_fingerprint.py -v    # Fingerprint unit tests
pytest tests/test_models.py -v         # Schema validation tests
pytest tests/test_pipeline.py -v       # Pipeline integration tests
pytest tests/test_api.py -v            # API endpoint tests
```

---

## Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| Language | Python 3.11 | Core language |
| API Framework | FastAPI | REST API with auto-docs |
| Database | MongoDB | Document store for listings |
| DB Driver (API) | Motor | Async MongoDB for FastAPI |
| DB Driver (Scrapers) | PyMongo | Sync MongoDB for scrapers |
| Static Scraping | BeautifulSoup4 | HTML parsing |
| Dynamic Scraping | Selenium | JavaScript-rendered pages |
| Driver Management | webdriver-manager | Auto ChromeDriver |
| Scheduling | APScheduler | 12-hour scrape cycles |
| Validation | Pydantic | Schema validation |
| Containerization | Docker + Compose | Deployment |
| Testing | pytest + httpx | Unit/integration/API tests |

---

## FYP-I Roadmap (Phase 2 — Not in current scope)

- [ ] spaCy NER-based skill extraction from descriptions
- [ ] TF-IDF domain classifier (web dev, data science, etc.)
- [ ] Content-based filtering recommendation engine
- [ ] Collaborative filtering layer
- [ ] React.js dashboard (matched + near-miss listings)
- [ ] Student registration and skill profile management
- [ ] Notification system for new matches

---

## License

This project is part of a Final Year Project (FYP) at university.

## Version

`v0.1.0` — Phase 1: Backend Data Pipeline