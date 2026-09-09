# SkillSync — Comprehensive Development Plan & Implementation Status
### AI-Driven Internship & Tech Event Discovery Platform

---

## 1. Project Understanding & Current Status

**Core Problem:** University students hunting for internships, hackathons, and tech opportunities are forced to juggle multiple fragmented platforms. Even when they find listings, generic keyword search fails to inform them whether they possess the required skills or what precise skills they need to learn to qualify.

**What SkillSync Does:**
1. Aggregates live listings from 6 distinct platforms (Rozee.pk, Mustakbil.com, Internee.pk, Remotive, Devpost, Wuzzuf.net).
2. Cleans, deduplicates via SHA-256 fingerprinting, and standardizes descriptions.
3. Automatically extracts and normalizes technical skills using a curated taxonomy engine (`taxonomy.json`).
4. Manages student skill profiles and domain interests with authenticated sessions.
5. Ranks listings against the student profile using a content-based recommendation engine, splitting opportunities into **Strong Matches ($\ge 70\%$)** and **Near Misses ($40–69\%$)** with explicit missing skill gap alerts.
6. Delivers an authentic notifications feed streaming actual scraper execution logs and newly discovered matched opportunities (100% scraper-driven, zero synthetic data).
7. Provides a modern, responsive web application with a unified Feather/Lucide SVG line design system and dark/light modes.

**Current Implementation Milestone:**
- **Phase 1 (Data Pipeline & API)**: 100% Complete.
- **FYP-I Core Modules (Skills Extraction, Recommendation Engine, Profile Management, Notifications, and Web Frontend)**: 100% Complete.
- **Automated Test Suite**: 46 automated tests passing across all pipeline and API modules.

---

## 2. Requirement Analysis & Evolution

- **Decoupled Scraper Architecture**: Each scraper runs in its own try-catch block with isolated error logging; failure in one source never blocks or halts the others.
- **SHA-256 Deduplication**: Uniquely fingerprints listings by hashing normalized `title + source + url`, eliminating duplicates across repeated scrape cycles.
- **Scraper-Driven Authenticity**: All notifications and listings derive strictly from MongoDB collections (`db.listings` and `db.scraper_runs`), eliminating synthetic or placeholder records.
- **Immediate Profile Synchronization**: Edits to student skills, university, and field of study auto-save and immediately reflect in recommendation recomputations.
- **Unified Design System**: All navigation icons and form indicators use consistent 18×18 / 16×16 SVG vector line icons (`stroke="currentColor" stroke-width="2" fill="none"`).

---

## 3. Functional Requirements Status

| ID | Requirement | Status | Implementation Details |
|---|---|---|---|
| **FR1** | Multi-source scraping on schedule | **Completed** | 6 scrapers running via APScheduler with 12h cycle |
| **FR2** | Isolated scraper fault tolerance | **Completed** | Individual try-catch blocks with run logging in `db.scraper_runs` |
| **FR3** | Listing deduplication | **Completed** | SHA-256 fingerprinting in `scrapers/fingerprint.py` |
| **FR4** | Pydantic schema validation | **Completed** | Strict schemas in `scrapers/models.py` & `api/models.py` |
| **FR5** | Persistent document storage | **Completed** | MongoDB with indexed collections (`listings`, `students`, `scraper_runs`) |
| **FR6** | REST API with filtering | **Completed** | Filtering by source, keyword, domain in `api/routes/listings.py` |
| **FR7** | Paginated API responses | **Completed** | Standardized `page` and `page_size` pagination with total counts |
| **FR8** | API documentation | **Completed** | Auto-generated Swagger UI (`/docs`) & ReDoc (`/redoc`) |
| **FR9** | Multi-container orchestration | **Completed** | `docker-compose.yml` orchestrating API, Scrapers, and MongoDB |
| **FR10** | Automated test coverage | **Completed** | 46 tests passing in `pytest` |
| **FR11** | NLP/Taxonomy skill extraction | **Completed** | `scrapers/skills/extractor.py` & `taxonomy.json` |
| **FR12** | Student profile & auth management | **Completed** | `api/routes/students.py`, `api/auth.py`, `frontend/profile.html` |
| **FR13** | Real-time recommendation engine | **Completed** | Content-based match score calculation and categorization |
| **FR14** | Interactive Student Dashboard | **Completed** | `frontend/index.html` with matched & near-miss listings |
| **FR15** | Scraper sync & match notifications | **Completed** | `api/routes/notifications.py` & `frontend/notifications.html` |
| **FR16** | Recompute recommendations modal | **Completed** | `POST /students/{id}/recompute` with interactive popup dialog |

---

## 4. Non-Functional Requirements

- **Reliability & Resilience**: Individual scrapers handle network timeouts, user-agent rotation, and random delays. Database indexes prevent duplication under concurrent requests.
- **Performance**: Asynchronous FastAPI endpoints via Motor enable fast sub-50ms query latency for paginated listings and instant profile matching.
- **Maintainability**: Clear separation of concerns between scraper spiders, processing pipeline, skill taxonomy, API routes, and static frontend assets.
- **Data Integrity**: Schema enforcement via Pydantic rejects incomplete or malformed listing payloads before storage.
- **Aesthetics & Usability**: Responsive design system featuring custom CSS variables, dark/light theme switching, and unified Feather/Lucide vector stroke icons.

---

## 5. User Roles & Permissions

1. **Student (Authenticated)**:
   - Registers and logs in with email and password.
   - Manages personal skills, education (university, field of study), and domain interests.
   - Triggers recommendation recomputation passes.
   - Views personalized dashboard, saved opportunities, and scraper notification logs.
2. **Guest / Public**:
   - Can browse and search live opportunities and inspect scraper sources status.
3. **API Consumer / Client**:
   - Accesses public GET endpoints for listings, scraper metrics, and platform health.

---

## 6. Features & Modules Breakdown

### Module 1: Data Acquisition (Scrapers)
- **Rozee.pk Spider** (`Selenium`): Headless browser automation targeting Pakistan internships.
- **Mustakbil.com Spider** (`BeautifulSoup`): High-speed HTML parsing for local software roles.
- **Internee.pk Spider** (`Selenium`): Traversal of virtual technical internship tracks.
- **Remotive Spider** (`JSON API`): Ingestion of global remote engineering positions.
- **Devpost Spider** (`Selenium`): Extraction of hackathons, dates, prize pools, and themes.
- **Wuzzuf.net Spider** (`BeautifulSoup`): Regional MENA junior tech opportunities.

### Module 2: Skill Extraction & Normalization
- Curated technical skill taxonomy dictionary (`scrapers/skills/taxonomy.json`).
- Extraction engine (`scrapers/skills/extractor.py`) parsing raw job descriptions into standardized tags.
- Historical backfill script (`scripts/backfill.py`) ensuring all active database listings have extracted skills.

### Module 3: Student Management & Authentication
- Secure password hashing and session tokens (`api/auth.py`).
- Full CRUD profile management endpoints (`api/routes/students.py`).
- Frontend session storage and personalized sidebar user card.

### Module 4: Recommendation Engine & Recomputation
- Dynamic formula:
  $$\text{match\_score} = \text{round}\left(\frac{|\text{matched\_skills}|}{|\text{required\_skills}|} \times 100\right)$$
- Splits listings into Strong Matches ($\ge 70\%$) and Near Misses ($40–69\%$).
- Identifies exact missing skills to generate actionable learning gaps.
- `POST /students/{id}/recompute` endpoint evaluating all live listings with an interactive popup results modal.

### Module 5: Authentic Notifications System
- Scraper-driven notification engine (`api/routes/notifications.py`) pulling directly from `db.scraper_runs` and `db.listings`.
- Categorizes events into platform sync summaries and new student opportunity matches.
- Provides unread count metrics and individual read status toggles.

### Module 6: Web Application & Design System
- **Dashboard (`index.html`)**: Time-of-day greeting, real-time match counters, segmented filter pills (`All`, `Matched`, `Near-miss`), domain filter, and opportunity cards.
- **Discover (`browse.html`)**: Live keyword search, platform source filter tabs, sanitized descriptions, and detail modals.
- **Notifications (`notifications.html`)**: Comprehensive sync activity stream with filter tabs (`All`, `Scraper Sync`, `Matches`) and quick actions.
- **Profile & Skills (`profile.html`)**: Interactive education inputs with SVG icons, skill pills management with suggestions, and Recompute recommendations card + modal.
- **Scraper Sources (`sources.html`)**: Platform health, active listing counts, and sync history.
- **Unified SVG Vector Icons**: Standardized 18×18 and 16×16 stroke icons across the entire interface.
- **Dark/Light Mode**: Smooth, persistent theme switching.

---

## 7. Database Architecture

### Collection: `listings`
```json
{
  "_id": "ObjectId",
  "fingerprint": "String (unique index, SHA-256)",
  "title": "String",
  "company": "String",
  "source": "String (indexed: rozee, mustakbil, remotive, etc.)",
  "source_url": "String",
  "description_raw": "String",
  "location": "String",
  "domain_tag": "String",
  "skills": ["String"],
  "posted_date": "ISODate",
  "deadline": "ISODate",
  "is_active": "Boolean",
  "scraped_at": "ISODate"
}
```

### Collection: `students`
```json
{
  "_id": "ObjectId",
  "name": "String",
  "email": "String (unique index)",
  "password_hash": "String",
  "university": "String",
  "field_of_study": "String",
  "skills": ["String"],
  "domain_interests": ["String"],
  "preferred_domain": "String",
  "preferred_location": "String",
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

### Collection: `scraper_runs`
```json
{
  "_id": "ObjectId",
  "source": "String",
  "status": "String (success / error)",
  "listings_found": "Integer",
  "listings_new": "Integer",
  "error_message": "String (nullable)",
  "started_at": "ISODate",
  "completed_at": "ISODate"
}
```

---

## 8. API Architecture

### Endpoints Overview
- **Listings**:
  - `GET /listings` — Search and filter opportunities with pagination.
  - `GET /listings/{id}` — Opportunity detail.
  - `GET /sources` — Scraper metrics and source summaries.
  - `GET /health` — Liveness & database connection health check.
  - `GET /scrape/status` — Status of the most recent scraper cycle.
- **Student Profile & Recommendation Engine**:
  - `POST /students/register` — Student registration.
  - `POST /students/login` — Authentication and session validation.
  - `GET /students/{id}` — Student profile.
  - `PUT /students/{id}/profile` — Update education, degree, and preferences.
  - `PUT /students/{id}/skills` — Update skill list.
  - `POST /students/{id}/recompute` — Dynamic recommendation pass returning evaluated count, match count, near-miss count, and top cards.
- **Notifications**:
  - `GET /notifications` — Live scraper sync logs and opportunity matches.
  - `GET /notifications/stats` — Unread count and summary metrics.
  - `PUT /notifications/{id}/read` — Mark notification as read.

---

## 9. Testing & Quality Assurance

- **Framework**: `pytest` + `httpx` (async API test client) + `mongomock`.
- **Test Suites**:
  1. `tests/test_students.py` — Student registration, login, profile updates, and recommendation recomputation.
  2. `tests/test_api.py` — Listings filtering, pagination, sources, and health checks.
  3. `tests/test_pipeline.py` — Processing pipeline, deduplication, and schema validation.
  4. `tests/test_fingerprint.py` — SHA-256 fingerprint generation and collision safety.
  5. `tests/test_models.py` — Pydantic schema validation.
- **Results**: **46 passed in 4.97s**.

---

## 10. Development Roadmap & Future Milestones

### Phase 1: Data Pipeline & Ingestion (Completed)
- [x] Multi-source scrapers (6 platforms)
- [x] SHA-256 deduplication
- [x] Pydantic validation & Motor MongoDB storage
- [x] APScheduler 12-hour cycle
- [x] Docker Compose multi-container setup

### Phase 2: Core Platform & NLP (Completed)
- [x] Skill taxonomy & extraction engine (`taxonomy.json`)
- [x] Student registration, login, and profile management
- [x] Content-based recommendation engine (Strong Fits vs. Near Misses)
- [x] Interactive Recompute Recommendations modal
- [x] Authentic scraper-driven notifications system
- [x] Full interactive frontend web application
- [x] Unified Feather/Lucide SVG line icon design system
- [x] Dark/Light mode persistence

### Phase 3: Advanced Intelligence & Scaling (Upcoming FYP-II Scope)
- [ ] Collaborative filtering layer based on student bookmarking and application behavior
- [ ] Automated resume parsing for one-click profile skill ingestion
- [ ] Email/Telegram webhook alerts for instant notification delivery
- [ ] Cloud deployment (AWS / DigitalOcean / Managed MongoDB Atlas)
- [ ] CI/CD pipeline with GitHub Actions
