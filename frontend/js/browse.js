/**
 * SkillSync — Discover Page Logic (Live Scraped Listings & Peer Recommendations)
 *
 * Implements:
 * 1. Live opportunities fetched directly from scrapers stored in MongoDB
 * 2. Real scraped descriptions (description_raw) rendered on cards and detail modals
 * 3. Skill gap analysis comparing extracted listing skills against student profile
 * 4. Interactive search & platform source filtering
 * 5. Opportunity bookmarking & interactive help popup
 */

let allDiscoverItems = [];
let activeCardId = null;
let currentSource = "";
let currentKeyword = "";
let activeOnly = true;

// Fallback student skills if not yet configured in localStorage
const DEFAULT_STUDENT_SKILLS = [
    "Python", "React", "TypeScript", "Git", "SQL", "NLP", "REST APIs", "CSS", "HTML", "Node.js", "Pandas"
];

document.addEventListener("DOMContentLoaded", async function () {
    setupFilterControls();
    setupHelpPopup();
    await loadDiscoverListings();
});

/**
 * Setup search input and source filtering controls.
 */
function setupFilterControls() {
    const searchInput = document.getElementById("discover-search");
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener("input", function () {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                currentKeyword = searchInput.value.trim();
                loadDiscoverListings();
            }, 350);
        });
    }

    const sourceTabs = document.querySelectorAll("#discover-source-tabs .source-tab");
    sourceTabs.forEach(tab => {
        tab.addEventListener("click", function () {
            sourceTabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            currentSource = tab.dataset.source || "";
            loadDiscoverListings();
        });
    });

    const activeToggle = document.getElementById("discover-active-toggle");
    if (activeToggle) {
        activeToggle.addEventListener("click", function () {
            activeOnly = !activeOnly;
            activeToggle.classList.toggle("active", activeOnly);
            const labelEl = activeToggle.querySelector(".discover-active-label");
            if (labelEl) {
                labelEl.textContent = activeOnly ? "Active only" : "All (incl. expired)";
            }
            loadDiscoverListings();
        });
    }
}

/**
 * Fetch and render live opportunities scraped from the data pipeline.
 */
async function loadDiscoverListings() {
    const container = document.getElementById("discover-listings");
    if (!container) return;

    // Show loading spinner
    container.innerHTML = `
        <div class="loading-container" style="grid-column: 1/-1; text-align: center; padding: 48px 0;">
            <div class="spinner"></div>
            <p style="margin-top: 16px; color: var(--text-secondary);">Loading scraped opportunities...</p>
        </div>
    `;

    try {
        const filters = {
            page: 1,
            page_size: 60
        };
        if (currentSource) filters.source = currentSource;
        if (currentKeyword) filters.keyword = currentKeyword;
        if (activeOnly) filters.active_only = true;

        const data = await fetchListings(filters);

        if (!data || !data.listings || data.listings.length === 0) {
            allDiscoverItems = [];
            container.innerHTML = `
                <div class="empty-state" style="grid-column: 1/-1; text-align: center; padding: 48px 0;">
                    <div class="empty-icon">📭</div>
                    <h3>No listings found</h3>
                    <p style="color: var(--text-secondary); margin-top: 8px;">
                        ${currentKeyword || currentSource || activeOnly ? "No scraped listings matched your filters. Try a different keyword, source, or disable 'Active only'." : "Scrapers may still be collecting data. Check back soon!"}
                    </p>
                </div>
            `;
            return;
        }

        // Map listings directly from the scraper data
        allDiscoverItems = data.listings.map(l => {
            const dInfo = (typeof computeDeadlineInfo === "function")
                ? computeDeadlineInfo(l.deadline, l.posted_date || l.scraped_at)
                : { daysLeft: null, label: "Active", isExpired: false, isUrgent: false, badgeClass: "active" };

            return {
                id: l.id,
                title: l.title || "Untitled Opportunity",
                company: l.company || capitalize(l.source),
                source: l.source || "unknown",
                source_url: l.source_url || "#",
                description_raw: l.description_raw || "",
                descriptionSnippet: cleanDescription(l.description_raw) || "No description provided in original listing.",
                category: getListingCategory(l),
                domain: l.domain_tag || capitalize(l.source),
                location: l.location || "Remote",
                locationFormatted: formatLocation(l.location),
                date: formatDate(l.posted_date || l.scraped_at),
                deadline: l.deadline,
                deadlineInfo: dInfo,
                skills: Array.isArray(l.skills) ? l.skills : [],
                apply_url: l.source_url || "#"
            };
        });

        renderDiscoverCards(allDiscoverItems);

    } catch (error) {
        console.error("Failed to load scraped listings:", error);
        allDiscoverItems = [];
        container.innerHTML = `
            <div class="empty-state" style="grid-column: 1/-1; text-align: center; padding: 48px 0;">
                <div class="empty-icon">⚠️</div>
                <h3>Failed to load listings</h3>
                <p style="color: var(--text-secondary); margin-top: 8px;">
                    Could not connect to API at ${API_BASE}. Make sure the backend service is running.
                </p>
            </div>
        `;
    }
}

/**
 * Render cards into the discover grid.
 */
function renderDiscoverCards(items) {
    const container = document.getElementById("discover-listings");
    if (!container) return;

    container.innerHTML = items.map(item => createDiscoverCardHtml(item)).join("");

    // Attach click listeners to cards
    container.querySelectorAll(".discover-card").forEach(card => {
        const id = card.dataset.id;
        card.addEventListener("click", () => openListingModal(id));
    });
}

/**
 * Create HTML string for a single discover card using real scraped data.
 */
function createDiscoverCardHtml(item) {
    const isFirstActive = (activeCardId === item.id);
    const activeClass = isFirstActive ? "active-title" : "";

    // Build tags row
    const tags = [];
    if (item.category) tags.push(`<span class="discover-tag">${escapeHtml(item.category)}</span>`);
    if (item.location) {
        tags.push(`<span class="discover-tag" title="${escapeHtml(item.location)}">📍 ${escapeHtml(item.locationFormatted || item.location)}</span>`);
    }
    if (item.skills && item.skills.length > 0) {
        const topSkills = item.skills.slice(0, 2);
        topSkills.forEach(s => tags.push(`<span class="discover-tag">⚡ ${escapeHtml(s)}</span>`));
    }

    return `
        <div class="discover-card" data-id="${item.id}" id="card-${item.id}">
            <div class="discover-card-badge">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                </svg>
                <span>PEER SUGGESTION • ${escapeHtml(item.source.toUpperCase())}</span>
            </div>

            <div class="discover-card-title ${activeClass}">${escapeHtml(item.title)}</div>
            <div class="discover-card-company">${escapeHtml(item.company)}</div>
            <div class="discover-card-desc">${escapeHtml(item.descriptionSnippet)}</div>

            <div class="discover-card-tags">
                ${tags.join("")}
            </div>

            <div class="discover-card-footer">
                <div class="discover-card-date ${item.deadlineInfo ? item.deadlineInfo.badgeClass : ''}">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                        <line x1="16" y1="2" x2="16" y2="6"></line>
                        <line x1="8" y1="2" x2="8" y2="6"></line>
                        <line x1="3" y1="10" x2="21" y2="10"></line>
                    </svg>
                    <span>${escapeHtml(item.deadlineInfo ? item.deadlineInfo.label : item.date)}</span>
                </div>
                <button class="btn-discover-details" onclick="event.stopPropagation(); openListingModal('${item.id}')">
                    View details ↗
                </button>
            </div>
        </div>
    `;
}

/**
 * Open detail modal for an opportunity.
 */
async function openListingModal(listingId) {
    activeCardId = listingId;

    // Highlight the active card
    document.querySelectorAll(".discover-card").forEach(c => {
        const title = c.querySelector(".discover-card-title");
        if (c.dataset.id === listingId) {
            c.classList.add("is-active-modal");
            if (title) title.classList.add("active-title");
        } else {
            c.classList.remove("is-active-modal");
            if (title) title.classList.remove("active-title");
        }
    });

    const overlay = document.getElementById("modal-overlay");
    const modalContent = document.getElementById("modal-content");
    if (!overlay || !modalContent) return;

    // Find the item in memory or fetch fresh from API
    let item = allDiscoverItems.find(p => p.id === listingId);
    if (!item) {
        try {
            const apiData = await fetchListingById(listingId);
            if (apiData) {
                const dInfo = (typeof computeDeadlineInfo === "function")
                    ? computeDeadlineInfo(apiData.deadline, apiData.posted_date || apiData.scraped_at)
                    : { daysLeft: null, label: "Active", isExpired: false, isUrgent: false, badgeClass: "active" };

                item = {
                    id: apiData.id,
                    title: apiData.title || "Untitled Opportunity",
                    company: apiData.company || capitalize(apiData.source),
                    source: apiData.source || "unknown",
                    source_url: apiData.source_url || "#",
                    description_raw: apiData.description_raw || "",
                    descriptionSnippet: cleanDescription(apiData.description_raw) || "No description provided.",
                    category: getListingCategory(apiData),
                    domain: apiData.domain_tag || capitalize(apiData.source),
                    location: apiData.location || "Remote",
                    locationFormatted: formatLocation(apiData.location),
                    date: formatDate(apiData.posted_date || apiData.scraped_at),
                    deadline: apiData.deadline,
                    deadlineInfo: dInfo,
                    skills: Array.isArray(apiData.skills) ? apiData.skills : [],
                    apply_url: apiData.source_url || "#"
                };
            }
        } catch (e) {
            console.error("Could not fetch listing details:", e);
        }
    }

    if (!item) return;

    // Get student's current skills to compare
    let studentSkills = DEFAULT_STUDENT_SKILLS;
    try {
        const saved = localStorage.getItem("skillsync-student-skills");
        if (saved) studentSkills = JSON.parse(saved);
    } catch (e) {
        studentSkills = DEFAULT_STUDENT_SKILLS;
    }

    // Check if item is bookmarked
    const savedListings = getSavedListings();
    const isSaved = savedListings.includes(item.id);

    // Build modal tags
    const modalTags = [];
    if (item.category) modalTags.push(`<span class="discover-modal-tag">${escapeHtml(item.category)}</span>`);
    if (item.source) modalTags.push(`<span class="discover-modal-tag">🌐 ${escapeHtml(capitalize(item.source))}</span>`);
    if (item.location) modalTags.push(`<span class="discover-modal-tag">📍 ${escapeHtml(item.location)}</span>`);
    if (item.deadlineInfo && item.deadlineInfo.label) {
        modalTags.push(`<span class="discover-modal-tag ${item.deadlineInfo.badgeClass}">📅 ${escapeHtml(item.deadlineInfo.label)}</span>`);
    } else if (item.date) {
        modalTags.push(`<span class="discover-modal-tag">📅 ${escapeHtml(item.date)}</span>`);
    }

    // Build required skills chips (green if matched, red ⊗ if missing)
    let skillsHtml = "";
    if (item.skills && item.skills.length > 0) {
        skillsHtml = item.skills.map(skill => {
            const hasSkill = studentSkills.some(s => s.toLowerCase() === skill.toLowerCase());
            if (hasSkill) {
                return `
                    <span class="skill-req-pill matched">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                        ${escapeHtml(skill)}
                    </span>
                `;
            } else {
                return `
                    <span class="skill-req-pill missing">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="15" y1="9" x2="9" y2="15"></line>
                            <line x1="9" y1="9" x2="15" y2="15"></line>
                        </svg>
                        ${escapeHtml(skill)}
                    </span>
                `;
            }
        }).join("");
    } else {
        skillsHtml = `<p style="font-size: 0.875rem; color: var(--text-secondary); font-style: italic; margin: 0;">No specific skill prerequisites parsed from listing.</p>`;
    }

    // Format the scraped description authentically
    const descriptionContent = formatDescriptionForModal(item.description_raw);

    modalContent.innerHTML = `
        <button class="discover-modal-close" id="modal-close-btn" aria-label="Close modal">✕</button>

        <div class="discover-modal-header">
            <h2 class="discover-modal-title">${escapeHtml(item.title)}</h2>
            <div class="discover-modal-company">${escapeHtml(item.company)}</div>
        </div>

        <div class="discover-modal-tags">
            ${modalTags.join("")}
        </div>

        <div class="discover-modal-body">
            <div class="discover-modal-section">
                <h3 class="discover-modal-heading">About</h3>
                ${descriptionContent}
            </div>

            <div class="discover-modal-section">
                <h3 class="discover-modal-heading">Required skills</h3>
                <div class="discover-modal-skills">
                    ${skillsHtml}
                </div>
            </div>
        </div>

        <div class="discover-modal-footer">
            <a href="${item.apply_url || '#'}" target="_blank" rel="noopener noreferrer" class="btn-modal-apply">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="7" y1="17" x2="17" y2="7"></line>
                    <polyline points="7 7 17 7 17 17"></polyline>
                </svg>
                Apply now
            </a>
            <button class="btn-modal-save ${isSaved ? 'saved' : ''}" id="btn-modal-save" onclick="handleToggleSaveListing('${item.id}')">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="${isSaved ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
                </svg>
                <span id="save-btn-text">${isSaved ? 'Saved' : 'Save'}</span>
            </button>
        </div>
    `;

    overlay.classList.add("open");

    // Reset modal body scroll position to top
    const modalBody = modalContent.querySelector(".discover-modal-body");
    if (modalBody) modalBody.scrollTop = 0;

    // Close button listener
    const closeBtn = document.getElementById("modal-close-btn");
    if (closeBtn) closeBtn.addEventListener("click", closeModal);
}

/**
 * Determine a relevant category for the listing.
 */
function getListingCategory(listing) {
    if (listing.domain_tag && listing.domain_tag.toLowerCase() !== (listing.source || "").toLowerCase()) {
        return listing.domain_tag;
    }
    if (listing.source === "devpost") return "Hackathon";

    const titleLower = (listing.title || "").toLowerCase();
    if (/intern|internship|trainee|apprentice/i.test(titleLower)) return "Internship";
    if (/developer|engineer|full-stack|full stack|frontend|backend|golang|rails|react|python|software/i.test(titleLower)) return "Software Engineering";
    if (/devops|cloud|infrastructure|sre/i.test(titleLower)) return "DevOps & Cloud";
    if (/data|ai|machine learning|analytics|bi\b/i.test(titleLower)) return "Data & AI";
    if (/qa|quality|tester|testing/i.test(titleLower)) return "QA & Testing";
    if (/writer|copywriter|content/i.test(titleLower)) return "Content & Writing";
    if (/support|customer service|help desk|desk engineer/i.test(titleLower)) return "Technical Support";
    if (/sales|business development|ppc|marketing/i.test(titleLower)) return "Sales & Marketing";
    if (/accountant|finance|bookkeeper/i.test(titleLower)) return "Finance & Accounting";

    return listing.source === "remotive" ? "Remote Tech" : capitalize(listing.source || "Opportunity");
}

/**
 * Format location string to prevent long multi-region locations from blowing out cards.
 */
function formatLocation(loc) {
    if (!loc) return "Remote";
    const cleaned = loc.trim();
    if (cleaned.toLowerCase() === "worldwide") return "Worldwide (Remote)";

    if (cleaned.includes(",") && cleaned.length > 22) {
        const parts = cleaned.split(",").map(p => p.trim()).filter(Boolean);
        if (parts.length > 2) {
            return `${parts[0]}, ${parts[1]} (+${parts.length - 2})`;
        }
    }
    return cleaned;
}

/**
 * Format raw scraped description for clean display in modal.
 * Handles HTML from sources like Remotive cleanly and securely.
 */
function formatDescriptionForModal(rawText) {
    if (!rawText || !rawText.trim()) {
        return `<p class="discover-modal-text" style="font-style: italic; color: var(--text-secondary);">No description provided in original listing.</p>`;
    }

    // Strip agency promotional boilerplate and HTML comments if present
    let text = rawText
        .replace(/NOT YOUR TECH STACK\?[\s\S]*?(?:Reach out and we'll match you\.?|$)/gi, "")
        .replace(/<!--[\s\S]*?-->/g, "")
        .trim();

    if (!text) {
        return `<p class="discover-modal-text" style="font-style: italic; color: var(--text-secondary);">No description provided in original listing.</p>`;
    }

    // If description contains HTML tags (e.g., from Remotive)
    if (/<[a-z][\s\S]*>/i.test(text)) {
        const div = document.createElement("div");
        div.innerHTML = text;

        // Remove dangerous/extraneous tags and tracking pixels
        div.querySelectorAll("script, style, img, iframe, object, embed, link").forEach(el => el.remove());

        // Convert Remotive's custom heading divs into semantic headings
        div.querySelectorAll("div.h1, div.h2, div.h3, div.h4").forEach(hDiv => {
            const heading = document.createElement("h4");
            heading.innerHTML = hDiv.innerHTML;
            hDiv.parentNode.replaceChild(heading, hDiv);
        });

        // Remove empty spacer paragraphs
        div.querySelectorAll("p").forEach(p => {
            if (!p.textContent.trim()) p.remove();
        });

        // Strip inline styling so the content renders with our clean typography
        div.querySelectorAll("*").forEach(el => {
            el.removeAttribute("style");
            el.removeAttribute("class");
            el.removeAttribute("id");
            el.removeAttribute("dir");
        });

        const cleanedHtml = div.innerHTML.trim();
        if (cleanedHtml) {
            return `<div class="discover-modal-html-desc">${cleanedHtml}</div>`;
        }
    }

    // Plain text (e.g., from Mustakbil): split into paragraphs
    const paragraphs = text.split(/\n+/).map(p => p.trim()).filter(Boolean);
    if (paragraphs.length === 0) {
        return `<p class="discover-modal-text" style="font-style: italic; color: var(--text-secondary);">No description provided in original listing.</p>`;
    }

    return paragraphs.map(p => `<p class="discover-modal-text">${escapeHtml(p)}</p>`).join("");
}

/**
 * Close modal.
 */
function closeModal() {
    const overlay = document.getElementById("modal-overlay");
    if (overlay) overlay.classList.remove("open");
}

// Close modal when clicking outside or pressing Escape
document.addEventListener("click", function (e) {
    const overlay = document.getElementById("modal-overlay");
    if (overlay && e.target === overlay) {
        closeModal();
    }
});

document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
        closeModal();
        const popup = document.getElementById("help-popup");
        if (popup) popup.classList.remove("open");
    }
});

/**
 * Toggle saving a listing in localStorage.
 */
function handleToggleSaveListing(listingId) {
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
}

function getSavedListings() {
    try {
        const data = localStorage.getItem("skillsync-saved-listings");
        return data ? JSON.parse(data) : [];
    } catch (e) {
        return [];
    }
}

/**
 * Help Button and Popup Handler.
 */
function setupHelpPopup() {
    const helpBtn = document.getElementById("help-btn");
    const helpPopup = document.getElementById("help-popup");
    if (!helpBtn || !helpPopup) return;

    helpBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        helpPopup.classList.toggle("open");
    });

    document.addEventListener("click", function (e) {
        if (!helpPopup.contains(e.target) && e.target !== helpBtn) {
            helpPopup.classList.remove("open");
        }
    });
}

/**
 * Clean HTML and normalize whitespace for card previews.
 * Inserts spaces between block tags and breaks so words do not merge.
 */
function cleanDescription(text) {
    if (!text) return "";
    let formatted = text
        .replace(/NOT YOUR TECH STACK\?[\s\S]*?(?:Reach out and we'll match you\.?|$)/gi, " ")
        .replace(/<!--[\s\S]*?-->/g, " ")
        .replace(/<br\s*[\/]?>/gi, " ")
        .replace(/<\/(p|div|li|h[1-6]|tr|section|article)>/gi, " ")
        .replace(/<(p|div|li|h[1-6]|tr|section|article)[^>]*>/gi, " ")
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
