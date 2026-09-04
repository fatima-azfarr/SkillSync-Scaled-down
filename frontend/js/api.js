/**
 * SkillSync — API Helper
 * 
 * All functions to communicate with our FastAPI backend.
 * Every API call goes through this file so there's one place
 * to change the base URL or add headers.
 */

// Base URL for our FastAPI backend
// In Docker: the API runs on the same host, port 8000
// Locally: also port 8000
const API_BASE = "http://localhost:8000";


/**
 * Fetch paginated listings with optional filters.
 * 
 * @param {Object} filters - Query parameters
 * @param {string} [filters.source] - Filter by source platform
 * @param {string} [filters.keyword] - Search keyword
 * @param {number} [filters.page] - Page number (default 1)
 * @param {number} [filters.page_size] - Items per page (default 20)
 * @returns {Object} { listings, total, page, page_size, total_pages }
 */
async function fetchListings(filters = {}) {
    const params = new URLSearchParams();

    if (filters.source) params.append("source", filters.source);
    if (filters.keyword) params.append("keyword", filters.keyword);
    if (filters.domain) params.append("domain", filters.domain);
    params.append("page", filters.page || 1);
    params.append("page_size", filters.page_size || 20);

    const response = await fetch(`${API_BASE}/listings?${params.toString()}`);
    if (!response.ok) throw new Error(`API error: ${response.status}`);
    return await response.json();
}


/**
 * Fetch a single listing by its ID.
 * 
 * @param {string} id - MongoDB ObjectId as string
 * @returns {Object} Listing details
 */
async function fetchListingById(id) {
    const response = await fetch(`${API_BASE}/listings/${id}`);
    if (!response.ok) throw new Error(`API error: ${response.status}`);
    return await response.json();
}


/**
 * Fetch all scraper sources with listing counts.
 * 
 * @returns {Array} List of { name, total_listings, last_scraped }
 */
async function fetchSources() {
    const response = await fetch(`${API_BASE}/sources`);
    if (!response.ok) throw new Error(`API error: ${response.status}`);
    return await response.json();
}


/**
 * Fetch the last scrape status for each scraper.
 * 
 * @returns {Array} List of scraper run status objects
 */
async function fetchScrapeStatus() {
    const response = await fetch(`${API_BASE}/scrape/status`);
    if (!response.ok) throw new Error(`API error: ${response.status}`);
    return await response.json();
}


/**
 * Fetch API health check.
 * 
 * @returns {Object} { status, database, timestamp }
 */
async function fetchHealth() {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) throw new Error(`API error: ${response.status}`);
    return await response.json();
}


// ─── Helper functions ──────────────────────────────

/**
 * Format a date string to a readable format.
 * @param {string} dateStr - ISO date string
 * @returns {string} Formatted date like "Aug 15, 2026"
 */
function formatDate(dateStr) {
    if (!dateStr) return "—";
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
    });
}

/**
 * Format a relative time string.
 * @param {string} dateStr - ISO date string  
 * @returns {string} Like "2 hours ago", "3 days ago"
 */
function timeAgo(dateStr) {
    if (!dateStr) return "—";
    const now = new Date();
    const date = new Date(dateStr);
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return "just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return formatDate(dateStr);
}

/**
 * Get a tag color class based on the source name.
 * @param {string} source - Source platform name
 * @returns {string} CSS class like "tag-teal"
 */
function getSourceTagClass(source) {
    const map = {
        rozee: "tag-teal",
        mustakbil: "tag-blue",
        internee: "tag-green",
        remotive: "tag-purple",
        devpost: "tag-orange",
        wuzzuf: "tag-red",
    };
    return map[source?.toLowerCase()] || "tag-gray";
}

/**
 * Capitalize first letter of a string.
 */
function capitalize(str) {
    if (!str) return "";
    return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Truncate text to a maximum length.
 */
function truncate(text, maxLen = 120) {
    if (!text || text.length <= maxLen) return text || "";
    return text.substring(0, maxLen).trim() + "…";
}
