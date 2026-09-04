# SkillSync — Implementation-Ready Development Plan
### AI-Driven Internship & Tech Event Discovery Platform

---

## 1. Project Understanding

**Core problem:** University students hunting for internships, hackathons, and tech events must check dozens of scattered platforms, and even when they find listings, keyword search doesn't tell them whether they're actually qualified — or how close they are.

**What SkillSync does:** Aggregates listings from six sources (Rozee.pk, Mustakbil.com, Internee.pk, Remotive, Devpost, Wuzzuf.net), cleans and tags them with NLP, and ranks them against each student's skill profile using a three-layer recommendation engine (rule-based cold start → content-based filtering → collaborative filtering). Instead of a flat search result, students get a dashboard split into "matched" and "near-miss" listings, with the exact missing skills highlighted, plus automated alerts when new matches appear.

**Target users:** University students (primarily CS/tech-adjacent) looking for internships, hackathons, and remote tech roles.

**Expected outcome (end of the 6-week phase in scope):** A working, containerized data pipeline — six scrapers feeding a deduplicated, validated dataset into MongoDB, exposed through an async FastAPI service with filtering, pagination, and full API docs. The ML/NLP layer (skill extraction, classifier, recommendation engine, dashboard, notifications) is explicitly deferred to FYP-I.

**Important scoping note:** The proposal document itself draws this line clearly — Weeks 1–6 build *only* the data pipeline (Modules 1 and part of 2). Modules 2 (full NLP tagging), 3, 4, 5, and 6 are FYP-I work. This plan treats the 6-week pipeline as the MVP and treats the ML/dashboard/notification layer as a clearly-scoped Phase 2, not something to build now.

---

## 2. Requirement Analysis

**Assumptions made (proposal doesn't specify these explicitly):**
- "Isolated try-except block" per scraper means one scraper failing must never crash the scheduler or block the other five.
- "MD5 hashing removes duplicates" is assumed to hash a normalized combination of (title + company/source + posting URL), not the raw HTML, since raw HTML changes between scrapes even for the same listing.
- CAPTCHA bypass "via cookie reuse" on Rozee.pk assumes a human-authenticated session cookie is periodically refreshed manually or semi-automatically — this is inherently fragile and is flagged as a risk in Section 17.
- "Student skill profile" (needed for Module 4 in FYP-I) isn't described anywhere in this proposal — there's no user registration/profile flow defined. This is a real gap, not an oversight to silently patch.
- Rate limiting / politeness delays between scraper requests are assumed necessary (not stated) to avoid IP bans, especially on Selenium-driven sites.

**Ambiguities flagged (not silently resolved):**
- No mention of how many listings per platform per cycle, or how far back scrapers look (all current listings vs. only new since last run).
- No error-alerting mechanism defined (who gets notified if a scraper fails repeatedly — email? log only?).
- "Full Swagger docs" is stated, but no auth is defined for the API in this phase — is it intentionally public/read-only for now?

---

## 3. Functional Requirements (Phase 1 — the 6-week scope)

- FR1: System scrapes all six platforms on a 12-hour schedule via APScheduler.
- FR2: Each scraper runs independently; a failure in one does not stop the others.
- FR3: Listings are deduplicated via hash fingerprint before storage.
- FR4: Listings are validated against a defined schema (Pydantic) before persistence.
- FR5: Cleaned listings are stored in MongoDB.
- FR6: A REST API exposes listings with filters by source, keyword, and domain.
- FR7: API responses are paginated.
- FR8: API is documented via Swagger/OpenAPI and a Postman collection.
- FR9: The full stack (API + scrapers + MongoDB) runs via a single `docker-compose up`.
- FR10: An end-to-end test confirms scrape → dedupe → validate → store → serve works without manual intervention.

**Deferred to FYP-I (explicitly out of scope now):**
- FR11: NLP-based skill extraction (spaCy NER + skill lexicon).
- FR12: Domain classification (Logistic Regression / TF-IDF).
- FR13: Recommendation engine (KB / CBF / CF layers).
- FR14: React dashboard with matched/near-miss display.
- FR15: Notification system for new matches.
- FR16: Student registration and skill-profile intake.

---

## 4. Non-Functional Requirements

- **Reliability:** A single scraper's failure (site layout change, timeout, CAPTCHA block) must not take down the scheduled cycle for the other five.
- **Performance:** Scrape cycle for all six sources should complete comfortably within the 12-hour window, with headroom for retries.
- **Data integrity:** No duplicate listings in MongoDB; schema validation rejects malformed records rather than silently storing them.
- **Maintainability:** Scrapers are isolated modules sharing one pipeline (validate → dedupe → save), so adding a 7th source later doesn't require touching existing scrapers.
- **Observability:** Structured logging per scraper run (start/end time, listings found, listings after dedup, errors).
- **Portability:** Entire stack must run identically on any machine via Docker — no "works on my machine" dependency on local Python/Mongo installs.
- **Resilience to anti-bot measures:** Selenium scrapers need UA rotation, randomized delays, and fallback strategies (requests → rotate UA → headed browser → cookie session) as the proposal specifies.
- **Security (baseline for this phase):** No secrets committed to source control; environment variables used for DB URIs and any credentials.

---

## 5. User Roles & Permissions

The 6-week phase has **no end-user-facing roles** — it's a backend data pipeline with an API. Only one implicit role exists:

- **API consumer** (developer / future frontend): read-only access to listings via GET endpoints. No write/delete exposed publicly in this phase.

**Deferred roles (FYP-I, once the dashboard and profiles exist):**
- **Student** — registers, builds a skill profile, views matched/near-miss listings, receives alerts.
- **Admin** (possible future addition, not in either proposal phase) — would monitor scraper health, manage sources. Flagged as a missing requirement in Section 17, not assumed into scope.

---

## 6. Features / Modules Breakdown (Phase 1)

**Module 1 — Data Acquisition**
- Six independent scrapers (2 BeautifulSoup/Scrapy, 2 Selenium, 1 JSON API, 1 Selenium for Devpost).
- APScheduler triggers all six every 12 hours.
- Each scraper wrapped in its own try-except; failures logged, not raised.
- MD5 (or stronger, e.g. SHA-256) fingerprint computed per listing before storage to dedupe.

**Module 2 — Data Processing (pipeline portion only, not NLP)**
- Basic text cleaning (whitespace/encoding normalization) — full tokenize/stopword/NER work deferred to FYP-I per the proposal's own scope line.
- Pydantic schema validation.
- Storage into MongoDB.

**Module 4 (partial) — API Layer**
- FastAPI app exposing listings.
- Filters: source, keyword, domain (domain tagging itself is FYP-I, but the filter field can exist and simply be empty until then).
- Pagination.
- Async MongoDB access via Motor.

**Infrastructure**
- Dockerfiles for the API service and the scraper service, separately.
- `docker-compose.yml` orchestrating API + scrapers + MongoDB with named volumes.

---

## 7. User Flows (Phase 1)

Since there's no UI yet, the "user" is a developer or the future frontend consuming the API:

1. **Scrape cycle flow:** Scheduler fires → each scraper runs independently → raw listings passed to pipeline → cleaned → fingerprinted → duplicates dropped → validated → saved to MongoDB → run logged.
2. **API consumption flow:** Client sends GET `/listings` with optional filters/pagination → API queries MongoDB via Motor → returns paginated JSON → client renders or processes.
3. **Local dev flow:** Developer clones repo → `docker-compose up` → API and scrapers come up, MongoDB persists via volume → developer hits `/docs` for Swagger UI.

**Deferred (FYP-I) flow:** Student signs up → builds skill profile → dashboard shows matched/near-miss listings → student receives alert when a new match appears.

---

## 8. UI / Page Breakdown

**Phase 1 has no UI.** The only "interface" is the auto-generated Swagger/OpenAPI docs page from FastAPI, plus the exported Postman collection for manual testing.

**Deferred (FYP-I) screens** — named here so they're tracked, not designed yet:
- Login / Signup
- Skill Profile setup (degree, field, known skills)
- Main Dashboard (matched listings top, near-miss below with red skill-gap badges)
- Listing Detail (title, source, match score, domain tag, deadline, required skills, missing skills)
- Notifications / Alerts view
- Settings (profile edit, alert preferences)

---

## 9. Recommended Tech Stack

The proposal's own week-by-week stack is sound; the recommendations below keep it but tighten a few choices:

| Layer | Proposal's choice | Recommendation |
|---|---|---|
| Language | Python | Confirmed — good fit for scraping + async API + future NLP |
| Static scraping | BeautifulSoup4 + Scrapy | Confirmed. Consider standardizing on Scrapy for both static sources once the pipeline stabilizes, to consolidate retry/throttling logic in one place instead of two. |
| Dynamic scraping | Selenium + undetected-chromedriver | Confirmed for now. Flag: Selenium is heavy and slow at scale — if scrape volume grows, Playwright is worth evaluating in FYP-I for speed and better stealth defaults. Not a Phase 1 change. |
| Scheduling | APScheduler | Confirmed for single-instance deployment. If this ever needs to run across multiple containers/instances, APScheduler's in-process scheduling won't coordinate — note for future, not now. |
| Data validation | Pydantic | Confirmed. |
| Database | MongoDB | Confirmed — flexible schema suits listings with varying fields across 6 sources. |
| DB driver | Motor (async) | Confirmed — matches FastAPI's async model. |
| API framework | FastAPI | Confirmed. |
| Dedup hashing | MD5 | **Suggest SHA-256** instead — MD5 has known collision weaknesses. For dedup fingerprinting (not security-critical) this is low-risk, but SHA-256 costs nothing extra and avoids the question entirely. |
| Containerization | Docker + docker-compose | Confirmed. |
| Testing | pytest | Confirmed. |
| API testing | Postman | Confirmed. |

---

## 10. System Architecture

```
                          ┌─────────────────────┐
                          │     APScheduler      │
                          │  (12-hour trigger)    │
                          └──────────┬───────────┘
                                     │
        ┌──────────┬──────────┬─────┴─────┬──────────┬──────────┐
        ▼          ▼          ▼           ▼          ▼          ▼
   Rozee.pk   Mustakbil   Internee.pk  Remotive    Devpost    Wuzzuf.net
   (Selenium) (BS4)       (Selenium)   (JSON API)  (Selenium) (BS4)
        │          │          │           │          │          │
        └──────────┴──────────┴─────┬─────┴──────────┴──────────┘
                                     ▼
                        ┌─────────────────────────┐
                        │   Shared Pipeline         │
                        │  clean → fingerprint      │
                        │  → dedupe → validate       │
                        │  (Pydantic)                │
                        └────────────┬────────────┘
                                     ▼
                            ┌─────────────────┐
                            │    MongoDB        │
                            │  (listings coll.) │
                            └────────┬──────────┘
                                     ▼
                        ┌─────────────────────────┐
                        │  FastAPI (async, Motor)   │
                        │  GET /listings + filters   │
                        │  + pagination + Swagger    │
                        └────────────┬────────────┘
                                     ▼
                          (Future: React Dashboard,
                           Recommendation Engine — FYP-I)
```

Deployment shape: two Docker services (`scrapers`, `api`) plus a MongoDB container, wired via `docker-compose` with a named volume for MongoDB data persistence.

---

## 11. Database Design

**Collection: `listings`**

| Field | Type | Notes |
|---|---|---|
| `_id` | ObjectId | Mongo default |
| `fingerprint` | string (indexed, unique) | SHA-256 of normalized title+source+URL — dedup key |
| `title` | string | |
| `source` | string (indexed) | e.g. "rozee", "wuzzuf" |
| `source_url` | string | original listing link |
| `description_raw` | string | as scraped |
| `posted_date` | datetime, nullable | not all sources expose this reliably |
| `deadline` | datetime, nullable | |
| `location` | string, nullable | |
| `domain_tag` | string, nullable | empty in Phase 1; populated by classifier in FYP-I |
| `skills` | array[string] | empty in Phase 1; populated by NLP extraction in FYP-I |
| `scraped_at` | datetime | |
| `is_active` | boolean | for soft-marking listings that disappear on re-scrape |

**Indexes:** unique index on `fingerprint`; compound index on `source` + `scraped_at` for filtered/paginated queries.

**Deferred collections (FYP-I):**
- `students` — profile, degree, field, declared skills.
- `interactions` — for the collaborative-filtering layer (views, applies, saves).
- `alerts` — sent notifications log, to avoid re-alerting the same match.

---

## 12. API Design (Phase 1)

| Endpoint | Method | Purpose |
|---|---|---|
| `/listings` | GET | List listings; query params: `source`, `keyword`, `domain`, `page`, `page_size` |
| `/listings/{id}` | GET | Single listing detail |
| `/sources` | GET | List of active scraper sources and their last successful run time |
| `/health` | GET | Liveness/readiness check for Docker healthcheck |
| `/scrape/status` | GET | Last run summary per scraper (found / deduped / errors) — useful for debugging without digging through logs |

All read-only in Phase 1; no auth required yet since there's no write surface, but see Section 13 for what changes once write/admin endpoints appear.

---

## 13. Security Considerations

- No secrets (Mongo URI, any API keys) committed to the repo — use `.env` + `.gitignore`, loaded via Pydantic settings.
- Rozee.pk's cookie-reuse CAPTCHA bypass stores a session cookie — this must never be committed to source control or logged in plaintext; treat it as a credential.
- Rate-limit/backoff on all scrapers to avoid IP bans and to be a reasonably well-behaved client of third-party sites.
- Since `/listings` is public and read-only in this phase, the main exposure is scraper credentials and infra config, not user data (no user accounts exist yet).
- When Phase 2 (FYP-I) adds student accounts, this section will need real authentication (JWT or session-based) and authorization per role — flagged now so it isn't bolted on as an afterthought later.
- Docker: don't run containers as root; keep MongoDB port unexposed to the host except where needed for local dev.

---

## 14. Development Phases & Roadmap

Following the proposal's own 6-week structure, since it's already well-sequenced by dependency:

**Phase 1 (Week 1) — Foundation**
- JSON schema for listings (Pydantic models).
- SHA-256 (recommend over MD5) fingerprinting utility.
- Structured logger.
- Multithreaded file reader.
- Pipeline skeleton: raw input → validate → dedupe → save.

**Phase 2 (Week 2) — Static Scrapers**
- Mustakbil.com (BeautifulSoup).
- Wuzzuf.net (BeautifulSoup).
- Scrapy spider for concurrent, scalable requests.
- All output routed through Week 1 pipeline.

**Phase 3 (Week 3) — Dynamic Scrapers**
- Rozee.pk (Selenium, cookie-reuse for CAPTCHA).
- Internee.pk (Selenium).
- UA rotation, randomized delays, cursor mimicking.
- Fallback decision chain: requests → rotate UA → headed browser → cookie session.
- Wire APScheduler for the 12-hour cycle.

**Phase 4 (Week 4) — API Layer**
- FastAPI app, five endpoints (see Section 12).
- Motor for async Mongo queries.
- Swagger docs, Postman collection export.

**Phase 5 (Week 5) — Containerization**
- Separate Dockerfiles for API and scraper services.
- `docker-compose.yml` for the full stack.
- Named volumes for Mongo persistence.
- Architecture diagram: current monolith vs. future microservices split.

**Phase 6 (Week 6) — Buffer, Testing, Docs**
- Fix incomplete items from Weeks 1–5.
- End-to-end pipeline test.
- README for clone-and-run.
- Demo video.
- `v0.1.0` GitHub release tag.
- FYP-I report section draft.

**Phase 2 (FYP-I, out of this plan's scope but tracked):** spaCy skill extraction, TF-IDF domain classifier, CBF cosine-similarity engine, Jaccard skill gaps, React dashboard, notifications, collaborative filtering.

---

## 15. Testing Strategy

- **Unit tests:** fingerprinting function (same listing → same hash; different listings → different hash), Pydantic schema validation (rejects malformed records), individual scraper parsers against saved sample HTML fixtures (so tests don't depend on live sites).
- **Integration tests:** pipeline end-to-end with a mocked scraper output → validate → dedupe → save to a test MongoDB instance.
- **API tests:** each endpoint via pytest + httpx test client — filters, pagination bounds, 404 on missing listing ID.
- **End-to-end test:** full `docker-compose up` → trigger a manual scrape → confirm listings appear via the API.
- **Failure-case tests:** a scraper that raises mid-run must not prevent the other five from completing; a malformed listing must be rejected, not silently stored.
- **Edge cases:** empty scrape result (site returned nothing), duplicate listings across two consecutive cycles, listings missing optional fields (deadline, location).

---

## 16. Deployment Plan

- **Local/dev:** `docker-compose up` brings up MongoDB, the scraper service, and the API service together.
- **Environment config:** `.env` file (git-ignored) for `MONGO_URI`, scraper delays/timeouts, and any session cookies.
- **Persistence:** named Docker volume for MongoDB data so restarts don't lose scraped history.
- **Healthchecks:** `/health` endpoint wired into the API container's Docker healthcheck.
- **Versioning:** tag `v0.1.0` at the end of Week 6 per the proposal.
- **Beyond Phase 1 (not required now, noting for later):** if this moves beyond local/demo use, a managed MongoDB (Atlas) and a small VM or container host (Railway/Render/a university server) would replace the local Docker Mongo instance.

---

## 17. Potential Risks & Missing Requirements

**Risks:**
- **CAPTCHA/cookie fragility (Rozee.pk):** cookie-reuse bypass will break whenever the session expires or Rozee changes its CAPTCHA flow — this is the single most fragile part of the whole pipeline and deserves monitoring/alerting, not a "set and forget" assumption.
- **Site layout changes:** any of the six sources changing their HTML/JS structure silently breaks that scraper. No requirement currently exists for detecting "zero listings returned" as a possible break vs. a genuinely quiet day.
- **IP bans / anti-bot escalation:** six scrapers hitting sites every 12 hours is a detectable pattern; sites may tighten defenses over time.
- **Selenium performance at scale:** as scrape volume grows, headed-browser Selenium runs are slow and resource-heavy — a scaling concern for later, not now.

**Missing requirements (proposal doesn't address these — flagged, not silently filled in):**
- No student registration/profile flow defined anywhere, even though the FYP-I recommendation engine depends entirely on having skill profiles to match against.
- No admin/monitoring role or dashboard for scraper health — currently the only visibility is logs and the `/scrape/status` endpoint proposed above.
- No data retention policy — do old/expired listings get archived, deleted, or kept forever with `is_active: false`?
- No specified volume expectations (listings per cycle) to size infrastructure against.
- No alerting mechanism if a scraper fails repeatedly across multiple cycles (currently: logged only).

---

## 18. Final Implementation Checklist (Phase 1 scope)

- [ ] Pydantic listing schema defined
- [ ] SHA-256 fingerprinting utility (recommended over MD5)
- [ ] Structured logger in place
- [ ] Pipeline skeleton: validate → dedupe → save
- [ ] Mustakbil.com scraper (BeautifulSoup)
- [ ] Wuzzuf.net scraper (BeautifulSoup)
- [ ] Scrapy spider for concurrent static scraping
- [ ] Rozee.pk scraper (Selenium + cookie-reuse CAPTCHA handling)
- [ ] Internee.pk scraper (Selenium)
- [ ] Remotive scraper (JSON API)
- [ ] Devpost scraper (Selenium)
- [ ] UA rotation + randomized delays + fallback decision chain
- [ ] APScheduler wired for 12-hour cycle
- [ ] MongoDB running with `listings` collection + unique fingerprint index
- [ ] FastAPI app with all five Phase 1 endpoints
- [ ] Motor async MongoDB integration
- [ ] Swagger docs auto-generated and verified
- [ ] Postman collection exported
- [ ] Dockerfile for API service
- [ ] Dockerfile for scraper service
- [ ] `docker-compose.yml` for full stack
- [ ] Named volume for MongoDB persistence
- [ ] Architecture diagram (monolith vs. future microservices)
- [ ] Unit tests (fingerprinting, schema validation, parsers)
- [ ] Integration test (pipeline end-to-end)
- [ ] API tests (all endpoints)
- [ ] Full end-to-end test via `docker-compose up`
- [ ] README (clone-and-run instructions, env vars documented)
- [ ] Demo video recorded
- [ ] `v0.1.0` tagged on GitHub
- [ ] FYP-I report section drafted
