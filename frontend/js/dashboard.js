/**
 * SkillSync — Dashboard Page Logic
 *
 * Implements:
 * 1. Dynamic Greeting & Stats Counters
 * 2. Matched Opportunities (>= 70% fit) with Match Badges
 * 3. Near-Miss Opportunities (40-69% fit) with Missing Skill Alerts & Gap View
 * 4. Trending Among Students Like You (Peer Suggestions)
 * 5. Detail Modal with Match Score Progress Bar & Required Skill Checkmarks
 * 6. Interactive Filter Pills (All, Matched, Near-miss), Keyword Search & Domain Filtering
 */

// Default student skills if not yet configured in Profile
const DEFAULT_STUDENT_SKILLS = [
    "Python", "React", "TypeScript", "Git",
    "SQL", "NLP", "REST APIs", "CSS",
    "HTML", "Node.js", "Pandas"
];

// Canonical curated dataset matching the design screenshots with active upcoming deadlines
const CANONICAL_MATCHED_OPPORTUNITIES = [
    {
        id: "curated-matched-1",
        title: "Frontend engineering intern",
        company: "Rozee.pk",
        source: "rozee",
        category: "Internship",
        domain: "Web Development",
        location: "Remote",
        deadlineDays: 14,
        deadlineFormatted: "14d left",
        deadlineInfo: { daysLeft: 14, label: "14d left", isExpired: false, isUrgent: false, badgeClass: "active" },
        matchScore: 92,
        skills: ["React", "TypeScript", "CSS", "Git", "REST APIs"],
        apply_url: "https://www.rozee.pk",
        description: "Join our growing engineering team to build modern, performant web interfaces using React and TypeScript. You'll work alongside senior engineers on customer-facing features, own small projects end-to-end, and contribute to our component library. We ship fast and value clean, maintainable code."
    },
    {
        id: "curated-matched-2",
        title: "MLH Fellowship — open source track",
        company: "MLH",
        source: "devpost",
        category: "Hackathon",
        domain: "Open Source",
        location: "Remote",
        deadlineDays: 21,
        deadlineFormatted: "21d left",
        deadlineInfo: { daysLeft: 21, label: "21d left", isExpired: false, isUrgent: false, badgeClass: "active" },
        matchScore: 85,
        skills: ["Git", "Python", "Open Source", "TypeScript"],
        apply_url: "https://fellowship.mlh.io",
        description: "A 12-week internship alternative for aspiring software engineers. Collaborate on real-world open source projects used by millions under the direct mentorship of experienced software engineers."
    },
    {
        id: "curated-matched-3",
        title: "Data science intern — NLP team",
        company: "Wuzzuf.net",
        source: "wuzzuf",
        category: "Internship",
        domain: "NLP",
        location: "Cairo, Egypt",
        deadlineDays: 18,
        deadlineFormatted: "18d left",
        deadlineInfo: { daysLeft: 18, label: "18d left", isExpired: false, isUrgent: false, badgeClass: "active" },
        matchScore: 78,
        skills: ["Python", "NLP", "Pandas", "SQL"],
        apply_url: "https://wuzzuf.net",
        description: "Work with our AI research division analyzing multilingual sentiment and conversational pipelines. Build production transformers, evaluate fine-tuned language models, and deploy data validation workflows."
    },
    {
        id: "curated-matched-4",
        title: "HackMIT 2026",
        company: "Devpost",
        source: "devpost",
        category: "Hackathon",
        domain: "AI",
        location: "Cambridge, MA",
        deadlineDays: 0,
        deadlineFormatted: "Today",
        deadlineInfo: { daysLeft: 0, label: "Today (Closing soon)", isExpired: false, isUrgent: true, badgeClass: "urgent" },
        matchScore: 82,
        skills: ["Python", "JavaScript", "React"],
        apply_url: "https://hackmit.org",
        description: "MIT's premier undergraduate hackathon bringing together 1,000+ hackers from around the globe to build groundbreaking software and hardware hacks over 36 hours."
    },
    {
        id: "curated-matched-5",
        title: "Google Summer of Code 2026",
        company: "Google",
        source: "google",
        category: "Event",
        domain: "Open Source",
        location: "Remote",
        deadlineDays: 28,
        deadlineFormatted: "28d left",
        deadlineInfo: { daysLeft: 28, label: "28d left", isExpired: false, isUrgent: false, badgeClass: "active" },
        matchScore: 75,
        skills: ["Git", "Python", "Open Source"],
        apply_url: "https://summerofcode.withgoogle.com",
        description: "Global online program focusing on bringing new contributors into open source software development. Spend 12+ weeks writing code for open source organizations with dedicated mentor guidance."
    }
];

const CANONICAL_NEARMISS_OPPORTUNITIES = [
    {
        id: "curated-nearmiss-1",
        title: "Backend engineering intern — payments",
        company: "Rozee.pk",
        source: "rozee",
        category: "Internship",
        domain: "Web Development",
        location: "Lahore, Pakistan",
        deadlineDays: 12,
        deadlineFormatted: "12d left",
        deadlineInfo: { daysLeft: 12, label: "12d left", isExpired: false, isUrgent: false, badgeClass: "active" },
        matchScore: 61,
        skills: ["Python", "SQL", "REST APIs", "Docker", "Redis", "Kubernetes"],
        missingSkills: ["Docker", "Redis", "Kubernetes"],
        apply_url: "https://www.rozee.pk",
        description: "Scale our high-volume payments settlement gateway. Help architect fault-tolerant distributed queues, ledger reconciliation, and merchant settlement APIs. Work with relational databases and distributed caches."
    },
    {
        id: "curated-nearmiss-2",
        title: "ML research intern — computer vision",
        company: "LinkedIn",
        source: "linkedin",
        category: "Internship",
        domain: "AI",
        location: "Remote",
        deadlineDays: 25,
        deadlineFormatted: "25d left",
        deadlineInfo: { daysLeft: 25, label: "25d left", isExpired: false, isUrgent: false, badgeClass: "active" },
        matchScore: 54,
        skills: ["Python", "Pandas", "PyTorch", "CUDA", "MLflow"],
        missingSkills: ["PyTorch", "CUDA", "MLflow"],
        apply_url: "https://www.linkedin.com/jobs",
        description: "Join our vision intelligence research group to prototype novel diffusion models and edge neural inference pipelines for automated scene understanding and image segmentation."
    },
    {
        id: "curated-nearmiss-3",
        title: "DevOps intern — cloud infrastructure",
        company: "Internshala",
        source: "internshala",
        category: "Internship",
        domain: "DevOps",
        location: "Remote",
        deadlineDays: 7,
        deadlineFormatted: "7d left",
        deadlineInfo: { daysLeft: 7, label: "7d left", isExpired: false, isUrgent: false, badgeClass: "active" },
        matchScore: 47,
        skills: ["Git", "Python", "AWS", "Terraform", "Docker"],
        missingSkills: ["AWS", "Terraform", "Docker"],
        apply_url: "https://internshala.com",
        description: "Maintain continuous integration pipelines and scalable infrastructure across multi-cloud environments. Automate provisioning, monitoring, security patching, and secrets rotation."
    }
];

const CANONICAL_TRENDING_SUGGESTIONS = [
    {
        id: "trending-1",
        badge: "PEER SUGGESTION",
        title: "Buildspace S5 — nights & weekends",
        subtitle: "Buildspace · AI",
        domain: "AI",
        apply_url: "https://buildspace.so"
    },
    {
        id: "trending-2",
        badge: "PEER SUGGESTION",
        title: "Codeforces educational round",
        subtitle: "Codeforces · Algorithms",
        domain: "Algorithms",
        apply_url: "https://codeforces.com"
    },
    {
        id: "trending-3",
        badge: "PEER SUGGESTION",
        title: "PM externship — product track",
        subtitle: "Extern · Product",
        domain: "Product",
        apply_url: "https://extern.com"
    },
    {
        id: "trending-4",
        badge: "PEER SUGGESTION",
        title: "Stanford TreeHacks 2026",
        subtitle: "Devpost · AI",
        domain: "AI",
        apply_url: "https://treehacks.com"
    }
];

// App State
let allMatchedItems = [...CANONICAL_MATCHED_OPPORTUNITIES];
let allNearMissItems = [...CANONICAL_NEARMISS_OPPORTUNITIES];
let allGeneralItems = [];
let activeFilter = "all";
let activeOnly = true;
let searchKeyword = "";
let selectedDomain = "";

/**
 * Check if the user is currently browsing as a guest.
 */
function isGuestUser() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get("guest") === "true") {
        localStorage.setItem("skillsync_guest", "true");
        localStorage.removeItem("skillsync-student-id");
        localStorage.removeItem("skillsync-student-name");
        localStorage.removeItem("skillsync-student-email");
        localStorage.removeItem("skillsync-student-skills");
        return true;
    }
    if (localStorage.getItem("skillsync_guest") === "true") {
        return true;
    }
    return !localStorage.getItem("skillsync-student-id");
}

document.addEventListener("DOMContentLoaded", async function () {
    await updateGreetingAndProfile();
    await initDashboardData();
    setupEventListeners();
});

/**
 * Personalize greeting based on student name and time of day.
 */
async function updateGreetingAndProfile() {
    const greetingEl = document.getElementById("dashboard-greeting");
    const subtitleEl = document.getElementById("dashboard-greeting-sub") || document.querySelector(".page-greeting p");
    const guestBanner = document.getElementById("guest-welcome-banner");

    if (isGuestUser()) {
        if (greetingEl) greetingEl.textContent = "Welcome, Guest";
        if (subtitleEl) {
            subtitleEl.innerHTML = `Explore live tech opportunities across all platforms. <a href="profile.html" style="color: var(--primary); font-weight: 600; text-decoration: underline;">Log in or register</a> to match with your skills.`;
        }
        if (guestBanner) guestBanner.style.display = "flex";
        return;
    }

    if (guestBanner) guestBanner.style.display = "none";

    let studentName = localStorage.getItem("skillsync-student-name");
    if (!studentName && localStorage.getItem("skillsync-student-id")) {
        try {
            const current = await safeFetch(`${API_BASE}/students/current`);
            if (current && current.name) {
                studentName = current.name;
                localStorage.setItem("skillsync-student-name", current.name);
                localStorage.setItem("skillsync-student-id", current.id);
                if (current.email) localStorage.setItem("skillsync-student-email", current.email);
            }
        } catch (e) {
            studentName = "Student";
        }
    }
    const firstName = (studentName || "Student").split(" ")[0];

    if (greetingEl) {
        greetingEl.textContent = `Welcome, ${firstName}`;
    }
    if (subtitleEl) {
        subtitleEl.textContent = "Here's what's new and relevant for you.";
    }
}

/**
 * Get active student skills from localStorage or defaults.
 */
function getActiveStudentSkills() {
    if (isGuestUser()) return [];
    try {
        const saved = localStorage.getItem("skillsync-student-skills");
        if (saved) {
            const parsed = JSON.parse(saved);
            if (Array.isArray(parsed) && parsed.length > 0) return parsed;
        }
    } catch (e) {
        console.warn("Could not read student skills:", e);
    }
    return DEFAULT_STUDENT_SKILLS;
}

/**
 * Initialize dashboard data:
 * 1. Curated baseline opportunities
 * 2. Dynamically score live scraped listings from the database
 * 3. Render stats, cards, and trending items
 */
async function initDashboardData() {
    const isGuest = isGuestUser();
    const studentSkills = getActiveStudentSkills();

    // Start with curated canonical items
    allMatchedItems = [...CANONICAL_MATCHED_OPPORTUNITIES];
    allNearMissItems = [...CANONICAL_NEARMISS_OPPORTUNITIES];
    allGeneralItems = [
        ...CANONICAL_MATCHED_OPPORTUNITIES,
        ...CANONICAL_NEARMISS_OPPORTUNITIES
    ];

    try {
        // Fetch live listings to enrich dashboard
        const data = await fetchListings({ page: 1, page_size: 50 });
        if (data && Array.isArray(data.listings)) {
            data.listings.forEach(listing => {
                const reqSkills = listing.skills || [];
                const matched = !isGuest && reqSkills.length > 0
                    ? reqSkills.filter(req => studentSkills.some(s => s.toLowerCase() === req.toLowerCase()))
                    : [];
                const missing = !isGuest && reqSkills.length > 0
                    ? reqSkills.filter(req => !studentSkills.some(s => s.toLowerCase() === req.toLowerCase()))
                    : [];
                const score = reqSkills.length > 0
                    ? Math.round((matched.length / reqSkills.length) * 100)
                    : 0;

                const dInfo = (typeof computeDeadlineInfo === "function")
                    ? computeDeadlineInfo(listing.deadline, listing.posted_date || listing.scraped_at)
                    : { daysLeft: null, label: "Active", isExpired: false, isUrgent: false, badgeClass: "active" };

                const opportunityObj = {
                    id: listing.id,
                    title: listing.title,
                    company: listing.company || capitalize(listing.source),
                    source: listing.source,
                    category: getListingCategory(listing),
                    domain: listing.domain_tag || capitalize(listing.source),
                    location: listing.location || "Remote",
                    deadline: listing.deadline,
                    deadlineInfo: dInfo,
                    deadlineDays: dInfo.daysLeft,
                    deadlineFormatted: dInfo.label,
                    matchScore: score,
                    skills: reqSkills,
                    missingSkills: missing,
                    apply_url: listing.source_url || "#",
                    description: cleanDescription(listing.description_raw) || "No description provided."
                };

                // Add to general list if not duplicate title
                if (!allGeneralItems.some(i => i.title.toLowerCase() === listing.title.toLowerCase())) {
                    allGeneralItems.push(opportunityObj);
                }

                // If logged in student, add to matched / near-miss
                if (!isGuest && reqSkills.length > 0) {
                    if (score >= 70 && !allMatchedItems.some(i => i.title.toLowerCase() === listing.title.toLowerCase())) {
                        allMatchedItems.push(opportunityObj);
                    } else if (score >= 40 && score < 70 && !allNearMissItems.some(i => i.title.toLowerCase() === listing.title.toLowerCase())) {
                        allNearMissItems.push(opportunityObj);
                    }
                }
            });
        }
    } catch (e) {
        console.warn("Backend listings fetch skipped or failed, using curated dataset:", e);
    }

    renderStats();

    const titleEl = document.getElementById("matched-section-title");
    const subtitleEl = document.getElementById("matched-section-subtitle");
    const nearMissSection = document.getElementById("section-nearmiss");

    if (isGuest) {
        if (titleEl) titleEl.textContent = "All Opportunities";
        if (subtitleEl) subtitleEl.textContent = "General listings across all platforms — log in to personalize with your skills";
        if (nearMissSection) nearMissSection.style.display = "none";
        renderGeneralOpportunities();
    } else {
        if (titleEl) titleEl.textContent = "Matched opportunities";
        if (subtitleEl) subtitleEl.textContent = "Based on your skills and interests";
        if (nearMissSection) nearMissSection.style.display = "block";
        renderMatchedOpportunities();
        renderNearMissOpportunities();
    }

    renderTrendingSuggestions();
}

/**
 * Render stats row numbers.
 */
function renderStats() {
    const matchedEl = document.getElementById("stat-matched");
    const nearmissEl = document.getElementById("stat-nearmiss");
    const newEl = document.getElementById("stat-new");
    const appliedEl = document.getElementById("stat-applied");

    const saved = getSavedListings();
    const appliedCount = Math.max(2, saved.length);

    if (isGuestUser()) {
        if (matchedEl) {
            matchedEl.textContent = allGeneralItems.length || "25+";
            const label = matchedEl.parentElement.querySelector(".stat-label");
            const desc = matchedEl.parentElement.querySelector(".stat-desc");
            if (label) label.textContent = "All Listings";
            if (desc) desc.textContent = "Live opportunities";
        }
        if (nearmissEl) {
            nearmissEl.textContent = "3";
            const label = nearmissEl.parentElement.querySelector(".stat-label");
            const desc = nearmissEl.parentElement.querySelector(".stat-desc");
            if (label) label.textContent = "Sources";
            if (desc) desc.textContent = "Mustakbil, Remotive, Rozee";
        }
        if (newEl) {
            newEl.textContent = "8";
            const label = newEl.parentElement.querySelector(".stat-label");
            const desc = newEl.parentElement.querySelector(".stat-desc");
            if (label) label.textContent = "Domains";
            if (desc) desc.textContent = "Web, AI, Cloud & more";
        }
        if (appliedEl) {
            appliedEl.textContent = "Guest";
            const label = appliedEl.parentElement.querySelector(".stat-label");
            const desc = appliedEl.parentElement.querySelector(".stat-desc");
            if (label) label.textContent = "Personal Fit";
            if (desc) desc.innerHTML = `<a href="profile.html" style="color:var(--primary);text-decoration:underline;">Log in to match</a>`;
        }
    } else {
        if (matchedEl) {
            matchedEl.textContent = allMatchedItems.length;
            const label = matchedEl.parentElement.querySelector(".stat-label");
            const desc = matchedEl.parentElement.querySelector(".stat-desc");
            if (label) label.textContent = "Matched";
            if (desc) desc.textContent = "Strong skill fit";
        }
        if (nearmissEl) {
            nearmissEl.textContent = allNearMissItems.length;
            const label = nearmissEl.parentElement.querySelector(".stat-label");
            const desc = nearmissEl.parentElement.querySelector(".stat-desc");
            if (label) label.textContent = "Near-miss";
            if (desc) desc.textContent = "Close to qualifying";
        }
        if (newEl) {
            newEl.textContent = 3;
            const label = newEl.parentElement.querySelector(".stat-label");
            const desc = newEl.parentElement.querySelector(".stat-desc");
            if (label) label.textContent = "New this week";
            if (desc) desc.textContent = "Added recently";
        }
        if (appliedEl) {
            appliedEl.textContent = appliedCount;
            const label = appliedEl.parentElement.querySelector(".stat-label");
            const desc = appliedEl.parentElement.querySelector(".stat-desc");
            if (label) label.textContent = "Applied";
            if (desc) desc.textContent = "In progress";
        }
    }
}

/**
 * Filter items by keyword, domain, and active freshness status.
 */
function filterListings(items) {
    return items.filter(item => {
        // Active & Fresh only filter
        if (activeOnly) {
            if (item.deadlineInfo && item.deadlineInfo.isExpired) {
                return false;
            }
        }

        // Keyword filter
        if (searchKeyword) {
            const kw = searchKeyword.toLowerCase();
            const matchesTitle = (item.title || "").toLowerCase().includes(kw);
            const matchesCompany = (item.company || "").toLowerCase().includes(kw);
            const matchesSkills = Array.isArray(item.skills) && item.skills.some(s => s.toLowerCase().includes(kw));
            if (!matchesTitle && !matchesCompany && !matchesSkills) return false;
        }

        // Domain filter
        if (selectedDomain) {
            const domainLower = selectedDomain.toLowerCase();
            const itemDomain = (item.domain || "").toLowerCase();
            const itemCategory = (item.category || "").toLowerCase();
            if (!itemDomain.includes(domainLower) && !itemCategory.includes(domainLower)) return false;
        }

        return true;
    });
}

/**
 * Render General Opportunities Grid (for Guests).
 */
function renderGeneralOpportunities() {
    const container = document.getElementById("matched-grid");
    if (!container) return;

    const filtered = filterListings(allGeneralItems);

    if (filtered.length === 0) {
        container.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <div class="empty-icon">🔍</div>
                <h3>No opportunities found</h3>
                <p>Try adjusting your search keyword or active filter.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = filtered.map(item => {
        const skillsHtml = (item.skills && item.skills.length > 0)
            ? `<div class="opp-skills-pills">${item.skills.slice(0, 3).map(s => `<span class="opp-skill-pill general">${escapeHtml(s)}</span>`).join("")}</div>`
            : `<div class="opp-skills-pills"><span class="opp-skill-pill general">Open to all tech backgrounds</span></div>`;

        const sourceLabel = item.source ? capitalize(item.source) : "Live";
        const deadlineClass = item.deadlineInfo ? item.deadlineInfo.badgeClass : '';
        const deadlineText = item.deadlineInfo
            ? item.deadlineInfo.label
            : (item.deadlineFormatted || (item.deadlineDays ? `${item.deadlineDays}d left` : "Active"));

        return `
            <div class="opportunity-card general-card" data-id="${item.id}">
                <div class="opp-top-row">
                    <h3 class="opp-title">${escapeHtml(item.title)}</h3>
                    <span class="match-badge general">${escapeHtml(sourceLabel)}</span>
                </div>
                <div class="opp-company">${escapeHtml(item.company || 'Tech Company')}</div>
                <div class="opp-tags">
                    <span class="opp-tag ${getTagClass(item.category)}">${escapeHtml(item.category || 'Engineering')}</span>
                    <span class="opp-tag">${escapeHtml(item.domain || 'Tech')}</span>
                    <span class="opp-tag">📍 ${escapeHtml(item.location || 'Remote')}</span>
                </div>
                ${skillsHtml}
                <div class="opp-footer">
                    <span class="opp-deadline ${deadlineClass}">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                            <line x1="16" y1="2" x2="16" y2="6"></line>
                            <line x1="8" y1="2" x2="8" y2="6"></line>
                            <line x1="3" y1="10" x2="21" y2="10"></line>
                        </svg>
                        ${escapeHtml(deadlineText)}
                    </span>
                    <button class="btn-opp-details" onclick="openOpportunityModal('${item.id}')">
                        View details ↗
                    </button>
                </div>
            </div>
        `;
    }).join("");
}

/**
 * Render Matched Opportunities Grid.
 */
function renderMatchedOpportunities() {
    const container = document.getElementById("matched-grid");
    if (!container) return;

    const filtered = filterListings(allMatchedItems);

    if (filtered.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🔍</div>
                <h3>No matched opportunities found</h3>
                <p>Try adjusting your search, domain, or active filter.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = filtered.map(item => `
        <div class="opportunity-card" data-id="${item.id}">
            <div class="opp-top-row">
                <h3 class="opp-title">${escapeHtml(item.title)}</h3>
                <span class="match-badge high">${item.matchScore}% match</span>
            </div>
            <div class="opp-company">${escapeHtml(item.company)}</div>
            <div class="opp-tags">
                <span class="opp-tag ${getTagClass(item.category)}">${escapeHtml(item.category)}</span>
                <span class="opp-tag">${escapeHtml(item.domain)}</span>
                <span class="opp-tag">📍 ${escapeHtml(item.location)}</span>
            </div>
            <div class="opp-footer">
                <span class="opp-deadline ${item.deadlineInfo ? item.deadlineInfo.badgeClass : ''}">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                        <line x1="16" y1="2" x2="16" y2="6"></line>
                        <line x1="8" y1="2" x2="8" y2="6"></line>
                        <line x1="3" y1="10" x2="21" y2="10"></line>
                    </svg>
                    ${item.deadlineInfo ? escapeHtml(item.deadlineInfo.label) : (item.deadlineDays ? `${item.deadlineDays}d left` : 'Active')}
                </span>
                <button class="btn-opp-details" onclick="openOpportunityModal('${item.id}')">
                    View details ↗
                </button>
            </div>
        </div>
    `).join("");
}

/**
 * Render Near-Miss Opportunities Grid.
 */
function renderNearMissOpportunities() {
    const container = document.getElementById("nearmiss-grid");
    if (!container) return;

    const filtered = filterListings(allNearMissItems);

    if (filtered.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🔍</div>
                <h3>No near-miss opportunities found</h3>
                <p>Try adjusting your search, domain, or active filter.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = filtered.map(item => {
        const missingText = (item.missingSkills && item.missingSkills.length > 0)
            ? item.missingSkills.join(", ")
            : "Specific prerequisites";

        return `
            <div class="opportunity-card" data-id="${item.id}">
                <div class="opp-top-row">
                    <h3 class="opp-title">${escapeHtml(item.title)}</h3>
                    <span class="match-badge medium">${item.matchScore}% match</span>
                </div>
                <div class="opp-company">${escapeHtml(item.company)}</div>
                <div class="opp-tags">
                    <span class="opp-tag ${getTagClass(item.category)}">${escapeHtml(item.category)}</span>
                    <span class="opp-tag">${escapeHtml(item.domain)}</span>
                    <span class="opp-tag">📍 ${escapeHtml(item.location)}</span>
                </div>
                <div class="missing-skills-box">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                        <line x1="12" y1="9" x2="12" y2="13"></line>
                        <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                    <span>Missing: <strong>${escapeHtml(missingText)}</strong></span>
                </div>
                <div class="opp-footer">
                    <span class="opp-deadline ${item.deadlineInfo ? item.deadlineInfo.badgeClass : ''}">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                            <line x1="16" y1="2" x2="16" y2="6"></line>
                            <line x1="8" y1="2" x2="8" y2="6"></line>
                            <line x1="3" y1="10" x2="21" y2="10"></line>
                        </svg>
                        ${item.deadlineInfo ? escapeHtml(item.deadlineInfo.label) : (item.deadlineDays ? `${item.deadlineDays}d left` : 'Active')}
                    </span>
                    <div class="opp-footer-actions">
                        <button class="btn-opp-gap" onclick="openSkillGapModal('${item.id}')">
                            View skill gap
                        </button>
                        <button class="btn-opp-details" onclick="openOpportunityModal('${item.id}')">
                            View details ↗
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join("");
}

/**
 * Render Trending Peer Suggestions.
 */
function renderTrendingSuggestions() {
    const container = document.getElementById("trending-grid");
    if (!container) return;

    container.innerHTML = CANONICAL_TRENDING_SUGGESTIONS.map(item => `
        <div class="peer-card" onclick="window.location.href='browse.html?keyword=${encodeURIComponent(item.title)}'">
            <div class="peer-badge">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                </svg>
                ${item.badge}
            </div>
            <div class="peer-title">${escapeHtml(item.title)}</div>
            <div class="peer-subtitle">${escapeHtml(item.subtitle)}</div>
        </div>
    `).join("");
}

/**
 * Open Opportunity Detail Modal (Matching Screenshot 5).
 */
function openOpportunityModal(oppId) {
    const item = allGeneralItems.find(i => i.id === oppId) ||
                 allMatchedItems.find(i => i.id === oppId) ||
                 allNearMissItems.find(i => i.id === oppId);
    if (!item) return;

    const overlay = document.getElementById("modal-overlay");
    const modalContent = document.getElementById("modal-content");
    if (!overlay || !modalContent) return;

    const isGuest = isGuestUser();
    const studentSkills = isGuest ? [] : getActiveStudentSkills();
    const isSaved = getSavedListings().includes(item.id);
    const isHighMatch = (item.matchScore || 0) >= 70;

    let matchSectionHtml = "";
    let skillsHtml = "";

    if (isGuest) {
        matchSectionHtml = `
            <div class="modal-guest-callout">
                <div class="modal-guest-callout-text">
                    <strong>💡 Exploring as Guest</strong>
                    <span>Log in or create an account to add your skills and get an instant AI match score for this role.</span>
                </div>
                <a href="profile.html" class="btn-modal-login">Log In →</a>
            </div>
        `;
        skillsHtml = (item.skills && item.skills.length > 0)
            ? item.skills.map(skill => `<span class="modal-skill-pill neutral">• ${escapeHtml(skill)}</span>`).join("")
            : `<span style="font-size: 0.85rem; color: var(--text-muted);">No specific skills required — open to all tech backgrounds.</span>`;
    } else {
        const alignmentText = isHighMatch
            ? "Strong match — your skills align well with this opportunity."
            : "Almost there — close to qualifying, missing a few skills.";

        skillsHtml = (item.skills && item.skills.length > 0)
            ? item.skills.map(skill => {
                const hasSkill = studentSkills.some(s => s.toLowerCase() === skill.toLowerCase());
                if (hasSkill) {
                    return `<span class="modal-skill-pill matched">✓ ${escapeHtml(skill)}</span>`;
                } else {
                    return `<span class="modal-skill-pill missing">⊗ ${escapeHtml(skill)}</span>`;
                }
            }).join("")
            : `<span style="font-size: 0.85rem; color: var(--text-muted);">No specific skills required.</span>`;

        matchSectionHtml = `
            <div class="modal-match-box ${isHighMatch ? 'high' : 'medium'}">
                <div class="modal-match-top">
                    <span class="modal-match-label">Match score</span>
                    <span class="modal-match-percent">${item.matchScore}%</span>
                </div>
                <div class="modal-match-track">
                    <div class="modal-match-fill" style="width: ${item.matchScore}%;"></div>
                </div>
                <p class="modal-match-desc">${alignmentText}</p>
            </div>
        `;
    }

    modalContent.innerHTML = `
        <button class="modal-dialog-close" id="modal-close-btn" aria-label="Close modal">✕</button>

        <div class="modal-dialog-header">
            <h2 class="modal-dialog-title">${escapeHtml(item.title)}</h2>
            <div class="modal-dialog-company">${escapeHtml(item.company)}</div>
        </div>

        <div class="modal-dialog-tags">
            <span class="opp-tag ${getTagClass(item.category)}">${escapeHtml(item.category)}</span>
            <span class="opp-tag">${escapeHtml(item.domain)}</span>
            <span class="opp-tag">📍 ${escapeHtml(item.location)}</span>
            <span class="opp-tag ${item.deadlineInfo ? item.deadlineInfo.badgeClass : ''}">📅 ${escapeHtml(item.deadlineInfo ? item.deadlineInfo.label : (item.deadlineFormatted || 'Active'))}</span>
        </div>

        <div class="modal-dialog-body">
            ${matchSectionHtml}

            <h3 class="modal-section-heading">About</h3>
            <p class="modal-description-p">${escapeHtml(item.description)}</p>

            <h3 class="modal-section-heading">Required skills</h3>
            <div class="modal-skills-list">
                ${skillsHtml}
            </div>
        </div>

        <div class="modal-dialog-footer">
            <a href="${item.apply_url || '#'}" target="_blank" rel="noopener noreferrer" class="btn-modal-apply">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="7" y1="17" x2="17" y2="7"></line>
                    <polyline points="7 7 17 7 17 17"></polyline>
                </svg>
                Apply now
            </a>
            <button class="btn-modal-save ${isSaved ? 'saved' : ''}" id="btn-modal-save" onclick="handleToggleSave('${item.id}')">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="${isSaved ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
                </svg>
                <span id="save-btn-text">${isSaved ? 'Saved' : 'Save'}</span>
            </button>
        </div>
    `;

    overlay.classList.add("open");

    const modalBody = modalContent.querySelector(".modal-dialog-body");
    if (modalBody) modalBody.scrollTop = 0;

    const closeBtn = document.getElementById("modal-close-btn");
    if (closeBtn) closeBtn.addEventListener("click", closeModal);
}

/**
 * Open Skill Gap Modal for near-miss opportunities.
 */
function openSkillGapModal(oppId) {
    const item = allNearMissItems.find(i => i.id === oppId);
    if (!item) return;

    const overlay = document.getElementById("modal-overlay");
    const modalContent = document.getElementById("modal-content");
    if (!overlay || !modalContent) return;

    const studentSkills = getActiveStudentSkills();
    const missing = item.missingSkills || [];
    const matched = item.skills.filter(s => !missing.includes(s));

    modalContent.innerHTML = `
        <button class="modal-dialog-close" id="modal-close-btn" aria-label="Close modal">✕</button>

        <div class="modal-dialog-header">
            <h2 class="modal-dialog-title">Skill Gap Analysis</h2>
            <div class="modal-dialog-company">${escapeHtml(item.title)} · ${escapeHtml(item.company)}</div>
        </div>

        <div class="modal-dialog-tags">
            <span class="match-badge medium">${item.matchScore}% Current Fit</span>
            <span class="opp-tag">📍 ${escapeHtml(item.location)}</span>
            <span class="opp-tag">🎯 Goal: 70%+</span>
        </div>

        <div class="modal-dialog-body">
            <div class="missing-skills-box" style="margin-bottom: 20px;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                    <line x1="12" y1="9" x2="12" y2="13"></line>
                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
                <div>
                    <div><strong>Missing Prerequisites:</strong> ${escapeHtml(missing.join(", "))}</div>
                    <div style="font-size: 0.775rem; margin-top: 3px; color: #78350F;">Mastering these ${missing.length} skill(s) will elevate your fit score to over 85%!</div>
                </div>
            </div>

            <h3 class="modal-section-heading">Skills You Already Have (${matched.length})</h3>
            <div class="modal-skills-list" style="margin-bottom: 16px;">
                ${matched.map(s => `<span class="modal-skill-pill matched">✓ ${escapeHtml(s)}</span>`).join("")}
            </div>

            <h3 class="modal-section-heading">Action Plan to Bridge the Gap</h3>
            <ul style="margin: 0 0 20px 20px; padding: 0; font-size: 0.875rem; color: var(--text-secondary); line-height: 1.6;">
                ${missing.map(skill => `
                    <li style="margin-bottom: 8px;">
                        <strong>${escapeHtml(skill)}:</strong> Complete a hands-on mini-project or course module to add to your profile.
                    </li>
                `).join("")}
            </ul>
        </div>

        <div class="modal-dialog-footer">
            <a href="profile.html" class="btn-modal-apply" style="background: #0D9488;">
                Update Profile Skills
            </a>
            <button class="btn-modal-save" onclick="closeModal()">
                Close
            </button>
        </div>
    `;

    overlay.classList.add("open");

    const closeBtn = document.getElementById("modal-close-btn");
    if (closeBtn) closeBtn.addEventListener("click", closeModal);
}

/**
 * Close modal.
 */
function closeModal() {
    const overlay = document.getElementById("modal-overlay");
    if (overlay) overlay.classList.remove("open");
}

/**
 * Setup event listeners for segmented pills, search, and domain dropdown.
 */
function setupEventListeners() {
    // Segmented Filter Pills (All, Matched, Near-miss)
    const pillsContainer = document.getElementById("header-filter-pills");
    if (pillsContainer) {
        pillsContainer.addEventListener("click", function (e) {
            const pill = e.target.closest(".filter-pill");
            if (!pill) return;

            pillsContainer.querySelectorAll(".filter-pill").forEach(p => p.classList.remove("active"));
            pill.classList.add("active");

            activeFilter = pill.dataset.filter || "all";
            applyFilterView();
        });
    }

    // Active & Fresh Only Toggle Button
    const activeToggle = document.getElementById("header-active-toggle");
    if (activeToggle) {
        activeToggle.addEventListener("click", function () {
            activeOnly = !activeOnly;
            activeToggle.classList.toggle("active", activeOnly);
            const labelEl = activeToggle.querySelector(".active-toggle-label");
            if (labelEl) {
                labelEl.textContent = activeOnly ? "Active only" : "All (incl. expired)";
            }
            if (isGuestUser()) {
                renderGeneralOpportunities();
            } else {
                renderMatchedOpportunities();
                renderNearMissOpportunities();
            }
        });
    }

    // Keyword Search
    const searchInput = document.getElementById("header-search");
    if (searchInput) {
        let debounce;
        searchInput.addEventListener("input", function () {
            clearTimeout(debounce);
            debounce = setTimeout(() => {
                searchKeyword = searchInput.value.trim();
                if (isGuestUser()) {
                    renderGeneralOpportunities();
                } else {
                    renderMatchedOpportunities();
                    renderNearMissOpportunities();
                }
            }, 300);
        });
    }

    // Domain Dropdown Filter
    const domainSelect = document.getElementById("header-domain");
    if (domainSelect) {
        domainSelect.addEventListener("change", function () {
            selectedDomain = domainSelect.value;
            if (isGuestUser()) {
                renderGeneralOpportunities();
            } else {
                renderMatchedOpportunities();
                renderNearMissOpportunities();
            }
        });
    }

    // Modal background close
    document.addEventListener("click", function (e) {
        const overlay = document.getElementById("modal-overlay");
        if (overlay && e.target === overlay) closeModal();
    });

    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") closeModal();
    });
}

/**
 * Apply visual filter according to active pill.
 */
function applyFilterView() {
    const matchedSection = document.getElementById("section-matched");
    const nearMissSection = document.getElementById("section-nearmiss");
    const trendingSection = document.getElementById("section-trending");

    if (isGuestUser()) {
        if (activeFilter === "all") {
            if (matchedSection) matchedSection.style.display = "block";
            if (nearMissSection) nearMissSection.style.display = "none";
            if (trendingSection) trendingSection.style.display = "block";
            renderGeneralOpportunities();
        } else if (activeFilter === "matched" || activeFilter === "near-miss") {
            if (matchedSection) matchedSection.style.display = "block";
            if (nearMissSection) nearMissSection.style.display = "none";
            if (trendingSection) trendingSection.style.display = "none";
            const container = document.getElementById("matched-grid");
            if (container) {
                const filterLabel = activeFilter === "matched" ? "matched" : "near-miss";
                container.innerHTML = `
                    <div class="empty-state guest-prompt-state" style="grid-column: 1 / -1;">
                        <div class="empty-icon">🎯</div>
                        <h3>Personalized Match View</h3>
                        <p>You are currently exploring as a guest without saved skills. <a href="profile.html" style="color: var(--primary); font-weight: 600; text-decoration: underline;">Log in or create an account</a> to add your skills and view personalized ${filterLabel} opportunities.</p>
                        <a href="profile.html" class="btn-primary" style="display: inline-block; width: auto; padding: 10px 24px; margin-top: 14px; text-decoration: none;">Log in / Register</a>
                    </div>
                `;
            }
        }
        return;
    }

    // Logged in student view
    if (activeFilter === "all") {
        if (matchedSection) matchedSection.style.display = "block";
        if (nearMissSection) nearMissSection.style.display = "block";
        if (trendingSection) trendingSection.style.display = "block";
        renderMatchedOpportunities();
        renderNearMissOpportunities();
    } else if (activeFilter === "matched") {
        if (matchedSection) matchedSection.style.display = "block";
        if (nearMissSection) nearMissSection.style.display = "none";
        if (trendingSection) trendingSection.style.display = "none";
        renderMatchedOpportunities();
    } else if (activeFilter === "near-miss") {
        if (matchedSection) matchedSection.style.display = "none";
        if (nearMissSection) nearMissSection.style.display = "block";
        if (trendingSection) trendingSection.style.display = "none";
        renderNearMissOpportunities();
    }
}

/**
 * Bookmark toggle helper.
 */
function handleToggleSave(listingId) {
    const saved = getSavedListings();
    const index = saved.indexOf(listingId);
    const btn = document.getElementById("btn-modal-save");
    const textEl = document.getElementById("save-btn-text");

    if (index > -1) {
        saved.splice(index, 1);
        if (btn) btn.classList.remove("saved");
        if (textEl) textEl.textContent = "Save";
    } else {
        saved.push(listingId);
        if (btn) btn.classList.add("saved");
        if (textEl) textEl.textContent = "Saved";
    }
    localStorage.setItem("skillsync-saved-listings", JSON.stringify(saved));
    renderStats();
}

function getSavedListings() {
    try {
        const saved = localStorage.getItem("skillsync-saved-listings");
        return saved ? JSON.parse(saved) : [];
    } catch (e) {
        return [];
    }
}

function getTagClass(category) {
    const catLower = (category || "").toLowerCase();
    if (catLower.includes("intern")) return "tag-internship";
    if (catLower.includes("hackathon")) return "tag-hackathon";
    if (catLower.includes("event")) return "tag-event";
    return "";
}

function getListingCategory(listing) {
    if (listing.domain_tag) return listing.domain_tag;
    const title = (listing.title || "").toLowerCase();
    if (/intern|internship/i.test(title)) return "Internship";
    if (/hackathon|challenge/i.test(title)) return "Hackathon";
    if (/fellowship|apprentice/i.test(title)) return "Fellowship";
    return "Opportunity";
}

function cleanDescription(text) {
    if (!text) return "";
    let formatted = text
        .replace(/NOT YOUR TECH STACK\?[\s\S]*?(?:Reach out and we'll match you\.?|$)/gi, " ")
        .replace(/<!--[\s\S]*?-->/g, " ")
        .replace(/<[^>]+>/g, " ");

    const div = document.createElement("div");
    div.innerHTML = formatted;
    const clean = div.textContent || div.innerText || "";
    return clean.replace(/\s+/g, " ").trim();
}

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
