# SkillSync — AI-Driven Internship & Tech Event Discovery Platform

SkillSync is an intelligent career discovery platform that aggregates internship, job, hackathon, and tech event listings from multiple scrapers, extracts required skills using a curated tech taxonomy, and ranks opportunities against university student profiles using a real-time recommendation engine.

Instead of generic keyword search, SkillSync computes exact percentage matches, categorizes opportunities into **Strong Matches** and **Near Misses**, provides actionable **Skill Gap** breakdowns, and streams authentic scraper notifications.

---

## Key Features

- **Multi-Source Data Pipeline**: Automated scrapers collecting listings across 6 platforms:
  - **Rozee.pk** (Selenium) — Internships & tech jobs in Pakistan
  - **Mustakbil.com** (BeautifulSoup) — Software engineering & IT listings in Pakistan
  - **Internee.pk** (Selenium) — Virtual internship programs
  - **Remotive** (JSON API) — Global remote software engineering roles
  - **Devpost** (Selenium) — Hackathons & student innovation challenges
  - **Wuzzuf.net** (BeautifulSoup) — Tech internships & junior roles across MENA
- **Skill Extraction & Taxonomy**: Curated tech taxonomy (`scrapers/skills/taxonomy.json`) and keyword extractor (`scrapers/skills/extractor.py`) that normalizes technical skills from raw descriptions into standardized tags.
- **Student Profile & Authentication**: Secure registration, login, and profile management with university, field of study, custom skill pills, suggestions, and domain interests.
- **Dynamic Recommendation Engine**:
  - Computes exact match percentages: $$\text{match\_score} = \text{round}\left(\frac{|\text{matched\_skills}|}{|\text{required\_skills}|} \times 100\right)$$
  - **Strong Matches ($\ge 70\%$)**: Highlights qualifying roles with verified skill badges.
  - **Near Misses ($40–69\%$)**: Flags high-potential roles within reach, highlighting the exact missing skills needed to qualify.
  - **Interactive Recompute Modal**: Triggerable on-demand from the Profile screen to re-evaluate opportunities in real time against updated skills.
- **Authentic Scraper-Driven Notifications**: Real-time sync logs and top match alerts derived 100% from actual scraper execution runs and database listings (zero mock/dummy placeholders).
- **Modern Responsive Web UI**:
  - **Unified SVG Line Icon Design System**: Crisp Feather/Lucide monochrome vector icons across all sidebar navigation items and profile fields.
  - **Light & Dark Mode**: Persistent theme switching with smooth transitions and dedicated dark palettes.
  - **5 Interactive Views**: Dashboard (`index.html`), Discover (`browse.html`), Notifications (`notifications.html`), Profile & Skills (`profile.html`), and Scraper Sources (`sources.html`).
- **Robust Pipeline**: SHA-256 fingerprint deduplication, Pydantic data validation, exponential retry backoff, and asynchronous MongoDB access via Motor.

---

## Architecture

```
                      APScheduler (12-hour cycle)
                                 │
    ┌────────────┬───────────┬───┴────────┬────────────┬────────────┐
    ▼            ▼           ▼            ▼            ▼            ▼
 Rozee.pk    Mustakbil   Internee.pk   Remotive     Devpost      Wuzzuf
(Selenium)     (BS4)     (Selenium)   (JSON API)   (Selenium)    (BS4)
    │            │           │            │            │            │
    └────────────┴───────────┴─────┬──────┴────────────┴────────────┘
                                   ▼
                    Shared Processing Pipeline
             (clean → fingerprint → dedupe → validate)
                                   │
                                   ▼
                      NLP Skill Taxonomy Extractor
                     (taxonomy.json → skill tags)
                                   │
                                   ▼
                           MongoDB Database
            (collections: listings, students, scraper_runs)
                                   │
                                   ▼
                        FastAPI REST API Service
         (listings, students auth/profile, recommendations, notifications)
                                   │
                                   ▼
                     SkillSync Web Application
     (Dashboard, Discover, Notifications, Profile, Sources, Dark/Light)
```

---

## Quick Start (Docker)

**Prerequisites:** Docker and Docker Compose installed.

```bash
# 1. Clone the repository
git clone https://github.com/fatima-azfarr/SkillSync-scaled-down.git
cd SkillSync-scaled-down

# 2. Create your .env file
cp .env.example .env

# 3. Start all services
docker-compose up

# 4. Access the application
# - API & Swagger Docs: http://localhost:8000/docs
# - Frontend Web App:   http://localhost:5500
```

---

## Quick Start (Local Development)

**Prerequisites:** Python 3.11, MongoDB installed and running locally, Google Chrome.

```bash
# 1. Clone the repository
git clone https://github.com/fatima-azfarr/SkillSync-scaled-down.git
cd SkillSync-scaled-down

# 2. Create virtual environment & activate
python3.11 -m venv venv
source venv/bin/activate       # macOS / Linux
# venv\Scripts\activate        # Windows

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Ensure MONGODB_URI=mongodb://localhost:27017

# 5. Start the FastAPI backend server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 6. Run a scraper or backfill (in a separate terminal)
source venv/bin/activate
python -m scrapers.main

# 7. Serve the frontend (in a separate terminal)
cd frontend
python3 -m http.server 5500
# Open http://localhost:5500 in your browser
```

---

## API Endpoints Reference

### Core Listings & Scrapers
| Endpoint | Method | Description |
|---|---|---|
| `/listings` | GET | List opportunities with filtering (`source`, `keyword`, `domain`, `page`, `page_size`) |
| `/listings/{id}` | GET | Retrieve complete listing details |
| `/sources` | GET | Active scraper sources and synchronization metrics |
| `/health` | GET | API and MongoDB connectivity health check |
| `/scrape/status` | GET | Summary of the most recent scraper runs |

### Student Profile & Recommendations
| Endpoint | Method | Description |
|---|---|---|
| `/students/register` | POST | Register a new student account |
| `/students/login` | POST | Authenticate student and initiate session |
| `/students/{id}` | GET | Retrieve student profile (university, skills, interests) |
| `/students/{id}/profile` | PUT | Update student full profile and educational info |
| `/students/{id}/skills` | PUT | Update student skills list |
| `/students/{id}/recompute` | POST | Trigger recommendation engine pass; returns match scores, strong fits, and near-misses |

### Notifications
| Endpoint | Method | Description |
|---|---|---|
| `/notifications` | GET | Scraper synchronization logs and student match notifications |
| `/notifications/stats` | GET | Unread notifications count and summary |
| `/notifications/{id}/read` | PUT | Mark an individual notification as read |

---

## Project Structure

```
SkillSync/
├── api/                          # FastAPI REST API service
│   ├── auth.py                   # Password hashing & authentication helpers
│   ├── config.py                 # Application configuration & env settings
│   ├── database.py               # Asynchronous MongoDB client (Motor)
│   ├── main.py                   # FastAPI application initialization & routes
│   ├── models.py                 # Pydantic request & response schemas
│   └── routes/
│       ├── health.py             # /health & /scrape/status
│       ├── listings.py           # /listings endpoints & filters
│       ├── notifications.py      # /notifications scraper activity endpoints
│       ├── sources.py            # /sources scraper metrics
│       └── students.py           # Student auth, profile & recommendation engine
│
├── frontend/                     # Modern Web Application
│   ├── css/
│   │   ├── discover.css          # Discover page & modal styles
│   │   ├── profile.css           # Profile screen & Recompute modal styles
│   │   └── style.css             # Unified design system & dashboard styles
│   ├── js/
│   │   ├── api.js                # Frontend API client library
│   │   ├── browse.js             # Discover page interaction & modal logic
│   │   ├── dashboard.js          # Dashboard matching, filtering & cards
│   │   ├── notifications.js      # Live notifications feed logic
│   │   ├── profile.js            # Profile editing & recommendation modal logic
│   │   └── theme.js              # Dark/Light mode toggle with SVG icons
│   ├── browse.html               # Discover opportunities page
│   ├── index.html                # Main student dashboard
│   ├── notifications.html        # Scraper activity & match notifications
│   ├── profile.html              # Profile & skills management
│   └── sources.html              # Scraper monitoring & status
│
├── scrapers/                     # Web Scraper Pipeline Service
│   ├── config.py                 # Scraper configuration
│   ├── fingerprint.py            # SHA-256 deduplication fingerprinting
│   ├── logger.py                 # Structured logging
│   ├── main.py                   # Scraper runner & APScheduler trigger
│   ├── models.py                 # Scraper data validation models
│   ├── pipeline.py               # Storage, deduplication & skill extraction pipeline
│   ├── utils.py                  # User-agent rotation, delays, Selenium helpers
│   ├── skills/                   # NLP & Taxonomy Skill Extraction
│   │   ├── extractor.py          # Regex/lexicon-based skill extraction
│   │   └── taxonomy.json         # Standardized technical skills dictionary
│   └── spiders/                  # Platform Spiders
│       ├── base.py               # Abstract scraper base class
│       ├── devpost.py            # Devpost hackathons (Selenium)
│       ├── internee.py           # Internee.pk internships (Selenium)
│       ├── mustakbil.py          # Mustakbil.com listings (BeautifulSoup)
│       ├── remotive.py           # Remotive remote tech jobs (JSON API)
│       ├── rozee.py              # Rozee.pk internships (Selenium)
│       └── wuzzuf.py             # Wuzzuf.net listings (BeautifulSoup)
│
├── scripts/                      # Utility Scripts
│   ├── backfill.py               # Historical listings skill backfill
│   └── mustakbil_backfill.py     # Mustakbil data processor
│
├── tests/                        # Comprehensive Test Suite
│   ├── conftest.py               # Shared pytest fixtures & mock database
│   ├── test_api.py               # API endpoint validation
│   ├── test_fingerprint.py       # Fingerprint hashing unit tests
│   ├── test_models.py            # Pydantic schema validation tests
│   ├── test_pipeline.py          # Processing pipeline integration tests
│   └── test_students.py          # Student auth, profile & recompute tests
│
├── docker-compose.yml            # Multi-container orchestration
├── requirements.txt              # Project dependencies
└── README.md                     # Project documentation
```

---

## Running Tests

All unit, integration, and API tests are automated using `pytest`:

```bash
# Run the entire test suite
pytest -v

# Run specific test modules
pytest tests/test_students.py -v       # Student auth & recommendation engine
pytest tests/test_api.py -v            # API endpoints
pytest tests/test_pipeline.py -v       # Pipeline & deduplication
pytest tests/test_models.py -v         # Schema validation
pytest tests/test_fingerprint.py -v    # Hashing
```

**Current Test Status:**
```
============================== 46 passed in 4.97s ==============================
```

---

## Technology Stack

| Layer | Technologies | Purpose |
|---|---|---|
| **Backend & API** | Python 3.11, FastAPI, Pydantic, Motor | High-performance asynchronous REST API |
| **Database** | MongoDB | Document store for flexible multi-source listings & students |
| **Data Acquisition** | BeautifulSoup4, Selenium, Requests, Scrapy | Multi-platform scraping (static HTML, JS-rendered, JSON API) |
| **NLP & Skills** | Custom Taxonomy Engine (`taxonomy.json`), Regex | Tech skill normalization & extraction from raw descriptions |
| **Matching Engine** | Content-based similarity & Jaccard skill-fit | Real-time match scoring, near-miss categorization, gap analysis |
| **Frontend Web App** | HTML5, Vanilla CSS3, Modern ES6+ JavaScript | Fast, accessible, framework-free UI with responsive design |
| **Design System** | Custom CSS Variables, Feather/Lucide SVG icons | Unified dark/light themes, sleek card layouts, micro-animations |
| **DevOps & Testing** | Docker, Docker Compose, Pytest, APScheduler | 12-hour scheduler, containerization, automated testing |

---

## License

This project is developed as a University Final Year Project (FYP).