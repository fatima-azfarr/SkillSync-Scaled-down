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
    if (filters.active_only !== undefined) params.append("active_only", filters.active_only);
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

// Helper for fetch that provides clear error messages on network failure
async function safeFetch(url, options) {
    try {
        return await fetch(url, options);
    } catch (err) {
        if (err.name === "TypeError" || (err.message && err.message.includes("fetch"))) {
            throw new Error(`Cannot connect to backend server at ${API_BASE}. Make sure the FastAPI backend is running.`);
        }
        throw err;
    }
}

// ─── Student / Auth functions ──────────────────────────────
// Same fetch + .ok-check pattern as the functions above.
// NOTE: there's no session token here (matches the API's current
// scope) - login just returns the student's profile including their
// id, which we then hold onto in localStorage (see profile.js).

/**
 * Register a new student account.
 *
 * @param {Object} data - { name, email, password, skills, preferred_domain, preferred_location }
 * @returns {Object} The created student's profile
 * @throws {Error} with a readable message on validation/duplicate-email errors
 */
async function registerStudent(data) {
    const response = await safeFetch(`${API_BASE}/students/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail || `Registration failed (${response.status})`);
    }

    return await response.json();
}

/**
 * Log in a student.
 *
 * @param {string} email
 * @param {string} password
 * @returns {Object} The student's profile
 * @throws {Error} with a readable message on invalid credentials
 */
async function loginStudent(email, password) {
    const response = await safeFetch(`${API_BASE}/students/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail || `Login failed (${response.status})`);
    }

    return await response.json();
}

/**
 * Fetch a student's profile by id.
 *
 * @param {string} studentId
 * @returns {Object} Student profile
 */
async function fetchStudent(studentId) {
    const response = await safeFetch(`${API_BASE}/students/${studentId}`);
    if (!response.ok) {
        const body = await response.json().catch(() => null);
        const err = new Error(body?.detail || `API error: ${response.status}`);
        err.status = response.status;
        throw err;
    }
    return await response.json();
}

/**
 * Update a student's profile (skills, domain, location).
 *
 * @param {string} studentId
 * @param {Object} data - { skills, preferred_domain, preferred_location }
 * @returns {Object} Updated student profile
 */
async function updateStudentProfile(studentId, data) {
    const response = await safeFetch(`${API_BASE}/students/${studentId}/profile`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        const body = await response.json().catch(() => null);
        const err = new Error(body?.detail || `Update failed (${response.status})`);
        err.status = response.status;
        throw err;
    }

    return await response.json();
}

/**
 * Recompute recommendations for a student.
 *
 * @param {string} studentId
 * @returns {Object} { status, message, timestamp }
 */
async function recomputeRecommendations(studentId) {
    const response = await safeFetch(`${API_BASE}/students/${studentId}/recompute`, {
        method: "POST",
    });

    if (!response.ok) {
        const body = await response.json().catch(() => null);
        const err = new Error(body?.detail || `Recompute failed (${response.status})`);
        err.status = response.status;
        throw err;
    }

    return await response.json();
}

// ─── Global Sidebar User & Sign Out Handling ──────────────────────────────
document.addEventListener("DOMContentLoaded", async function () {
    const urlParams = new URLSearchParams(window.location.search);
    const isGuestParam = urlParams.get("guest") === "true";
    if (isGuestParam) {
        localStorage.setItem("skillsync_guest", "true");
        localStorage.removeItem("skillsync-student-id");
        localStorage.removeItem("skillsync-student-name");
        localStorage.removeItem("skillsync-student-email");
        localStorage.removeItem("skillsync-student-skills");
    }

    const isGuest = localStorage.getItem("skillsync_guest") === "true" || !localStorage.getItem("skillsync-student-id");
    if (isGuest) {
        document.documentElement.classList.add("is-guest");
        document.body.classList.add("is-guest");
    } else {
        document.documentElement.classList.remove("is-guest");
        document.body.classList.remove("is-guest");
    }

    const nameEl = document.getElementById("sidebar-user-name");
    const avatarEl = document.getElementById("sidebar-user-avatar");
    const emailEl = document.getElementById("sidebar-user-email");
    const logoutBtn = document.getElementById("sidebar-logout-btn");

    if (isGuest) {
        if (nameEl) nameEl.textContent = "Guest";
        if (avatarEl) avatarEl.textContent = "G";
        if (emailEl) emailEl.textContent = "Explore mode";
        if (logoutBtn) {
            logoutBtn.innerHTML = `
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path>
                    <polyline points="10 17 15 12 10 7"></polyline>
                    <line x1="15" y1="12" x2="3" y2="12"></line>
                </svg>
                <span>Log in / Register</span>
            `;
            logoutBtn.addEventListener("click", function (e) {
                e.preventDefault();
                window.location.href = "profile.html";
            });
        }
    } else {
        let studentName = localStorage.getItem("skillsync-student-name");
        let studentEmail = localStorage.getItem("skillsync-student-email");

        if (studentName && nameEl) {
            nameEl.textContent = studentName.split(" ")[0] || studentName;
            if (avatarEl) {
                const initials = studentName.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2);
                avatarEl.textContent = initials || "S";
            }
        }
        if (studentEmail && emailEl) {
            emailEl.textContent = studentEmail;
        }

        if (logoutBtn) {
            logoutBtn.addEventListener("click", function (e) {
                e.preventDefault();
                localStorage.setItem("skillsync_guest", "true");
                localStorage.removeItem("skillsync-student-id");
                localStorage.removeItem("skillsync-student-name");
                localStorage.removeItem("skillsync-student-email");
                localStorage.removeItem("skillsync-student-skills");
                document.documentElement.classList.add("is-guest");
                document.body.classList.add("is-guest");
                updateGlobalNotificationBadges();
                if (window.location.pathname.endsWith("profile.html")) {
                    if (typeof showAuthView === "function") {
                        showAuthView();
                    } else {
                        window.location.reload();
                    }
                } else {
                    window.location.href = "profile.html";
                }
            });
        }
    }

    // Global Notification Badges & Header Bell Navigation
    updateGlobalNotificationBadges();
});

/**
 * Synchronize unread notification badge across all pages.
 * Suppressed completely for guests.
 */
function updateGlobalNotificationBadges() {
    const isGuest = localStorage.getItem("skillsync_guest") === "true" || !localStorage.getItem("skillsync-student-id");

    const sidebarNotifItems = document.querySelectorAll('a.nav-item[href*="notifications.html"]');
    const headerNotifBtns = document.querySelectorAll(".header-notification, #header-notification-btn");
    const sidebarBadges = document.querySelectorAll(".nav-item .nav-badge, #sidebar-notif-badge");
    const headerBadges = document.querySelectorAll(".header-notification .badge, #header-notif-badge");

    if (isGuest) {
        document.documentElement.classList.add("is-guest");
        document.body.classList.add("is-guest");
        sidebarNotifItems.forEach(el => el.style.display = "none");
        headerNotifBtns.forEach(el => el.style.display = "none");
        sidebarBadges.forEach(b => b.style.display = "none");
        headerBadges.forEach(b => b.style.display = "none");
        return;
    }

    document.documentElement.classList.remove("is-guest");
    document.body.classList.remove("is-guest");
    sidebarNotifItems.forEach(el => el.style.display = "");
    headerNotifBtns.forEach(el => el.style.display = "");

    const savedCount = localStorage.getItem("skillsync-unread-count");
    const count = savedCount !== null ? parseInt(savedCount, 10) : 2;

    sidebarBadges.forEach(b => {
        b.textContent = count;
        b.style.display = count > 0 ? "flex" : "none";
    });

    headerBadges.forEach(b => {
        b.textContent = count;
        b.style.display = count > 0 ? "flex" : "none";
    });

    // Wire all header notification bell buttons to navigate to notifications.html
    headerNotifBtns.forEach(btn => {
        btn.onclick = function () {
            window.location.href = "notifications.html";
        };
    });
}

/**
 * Compute dynamic deadline status and badge info from listing deadline or date.
 *
 * @param {string|Date|null} deadline - The application deadline.
 * @param {string|Date|null} postedOrScraped - Fallback date if deadline is null.
 * @returns {object} { daysLeft, label, isExpired, isUrgent, badgeClass }
 */
function computeDeadlineInfo(deadline, postedOrScraped) {
    if (!deadline) {
        // Rolling / Active opportunity without hard deadline (e.g. Remotive)
        return {
            daysLeft: null,
            label: "Rolling / Active",
            isExpired: false,
            isUrgent: false,
            badgeClass: "rolling"
        };
    }

    const deadlineDate = new Date(deadline);
    if (isNaN(deadlineDate.getTime())) {
        return {
            daysLeft: null,
            label: "Active",
            isExpired: false,
            isUrgent: false,
            badgeClass: "active"
        };
    }

    const now = new Date();
    // Normalize to midnight for accurate whole-day difference
    const dMidnight = new Date(deadlineDate.getFullYear(), deadlineDate.getMonth(), deadlineDate.getDate());
    const nowMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const diffMs = dMidnight - nowMidnight;
    const daysLeft = Math.round(diffMs / (1000 * 60 * 60 * 24));

    if (daysLeft < 0) {
        return {
            daysLeft,
            label: "Expired",
            isExpired: true,
            isUrgent: false,
            badgeClass: "expired"
        };
    } else if (daysLeft === 0) {
        return {
            daysLeft: 0,
            label: "Today (Closing soon)",
            isExpired: false,
            isUrgent: true,
            badgeClass: "urgent"
        };
    } else if (daysLeft <= 5) {
        return {
            daysLeft,
            label: `${daysLeft}d left`,
            isExpired: false,
            isUrgent: true,
            badgeClass: "urgent"
        };
    } else {
        return {
            daysLeft,
            label: `${daysLeft}d left`,
            isExpired: false,
            isUrgent: false,
            badgeClass: "active"
        };
    }
}
