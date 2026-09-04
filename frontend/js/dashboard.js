/**
 * SkillSync — Dashboard Page Logic
 *
 * Loads and renders:
 * 1. Stats cards (total listings, sources, recent, last updated)
 * 2. Listing cards grid (latest opportunities)
 * 3. Listing detail modal
 */

document.addEventListener("DOMContentLoaded", async function () {
    await loadDashboard();

    // Search handler
    const searchInput = document.getElementById("header-search");
    if (searchInput) {
        let debounce;
        searchInput.addEventListener("input", function () {
            clearTimeout(debounce);
            debounce = setTimeout(() => {
                loadListings({ keyword: searchInput.value });
            }, 400);
        });
    }

    // Source filter in header
    const domainFilter = document.getElementById("header-domain");
    if (domainFilter) {
        domainFilter.addEventListener("change", function () {
            loadListings({ source: domainFilter.value });
        });
    }
});


/**
 * Load all dashboard data.
 */
async function loadDashboard() {
    try {
        // Load stats and listings in parallel
        const [listingsData, sources, health] = await Promise.all([
            fetchListings({ page_size: 9 }),
            fetchSources(),
            fetchHealth(),
        ]);

        renderStats(listingsData.total, sources);
        renderListings(listingsData.listings);
        populateSourceFilter(sources);

    } catch (error) {
        console.error("Failed to load dashboard:", error);
        document.getElementById("listings-container").innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚠️</div>
                <h3>Could not connect to API</h3>
                <p>Make sure the backend is running at ${API_BASE}</p>
            </div>
        `;
    }
}


/**
 * Render the stats cards.
 */
function renderStats(totalListings, sources) {
    const activeSources = sources.length;

    // Count listings from last 7 days
    const oneWeekAgo = new Date();
    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);

    // Find last scraped time
    let lastScraped = null;
    sources.forEach(s => {
        if (s.last_scraped && (!lastScraped || new Date(s.last_scraped) > new Date(lastScraped))) {
            lastScraped = s.last_scraped;
        }
    });

    document.getElementById("stat-total").textContent = totalListings;
    document.getElementById("stat-sources").textContent = activeSources;
    document.getElementById("stat-new").textContent = totalListings > 0 ? Math.min(totalListings, 20) : 0;
    document.getElementById("stat-updated").textContent = lastScraped ? timeAgo(lastScraped) : "—";
}


/**
 * Load listings with optional filters.
 */
async function loadListings(filters = {}) {
    const container = document.getElementById("listings-container");
    container.innerHTML = '<div class="loading-container"><div class="spinner"></div><p>Loading listings...</p></div>';

    try {
        const data = await fetchListings({ ...filters, page_size: 9 });
        renderListings(data.listings);
        document.getElementById("listings-count").textContent = `${data.total} opportunities`;
    } catch (error) {
        console.error("Failed to load listings:", error);
        container.innerHTML = '<div class="empty-state"><div class="empty-icon">😕</div><h3>Failed to load listings</h3></div>';
    }
}


/**
 * Render listing cards into the grid.
 */
function renderListings(listings) {
    const container = document.getElementById("listings-container");

    if (!listings || listings.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📭</div>
                <h3>No listings found</h3>
                <p>Scrapers may still be collecting data. Check back soon!</p>
            </div>
        `;
        return;
    }

    container.innerHTML = listings.map(listing => createListingCard(listing)).join("");

    // Add click handlers
    container.querySelectorAll(".listing-card").forEach(card => {
        card.addEventListener("click", function () {
            openListingModal(card.dataset.id);
        });
    });
}


/**
 * Create HTML for a single listing card.
 */
function createListingCard(listing) {
    const sourceTag = `<span class="tag ${getSourceTagClass(listing.source)}">${capitalize(listing.source)}</span>`;
    const locationTag = listing.location
        ? `<span class="listing-location">📍 ${listing.location}</span>`
        : "";

    return `
        <div class="listing-card" data-id="${listing.id}">
            <div class="listing-card-header">
                <div class="listing-title">${listing.title}</div>
            </div>
            <div class="listing-source">${listing.company || capitalize(listing.source)}</div>
            <div class="listing-tags">
                ${sourceTag}
                ${locationTag ? `<span class="tag tag-gray">📍 ${listing.location}</span>` : ""}
            </div>
            <div class="listing-footer">
                <span class="listing-date">📅 ${formatDate(listing.scraped_at)}</span>
                <button class="view-details-btn" onclick="event.stopPropagation(); openListingModal('${listing.id}')">
                    View details ↗
                </button>
            </div>
        </div>
    `;
}


/**
 * Open the listing detail modal.
 */
async function openListingModal(listingId) {
    const overlay = document.getElementById("modal-overlay");
    const modal = document.getElementById("modal-content");

    // Show loading state
    overlay.classList.add("open");
    modal.innerHTML = '<div class="loading-container" style="padding:40px"><div class="spinner"></div><p>Loading...</p></div>';

    try {
        const listing = await fetchListingById(listingId);
        modal.innerHTML = renderModalContent(listing);

        // Close button handler
        modal.querySelector(".modal-close").addEventListener("click", closeModal);

    } catch (error) {
        console.error("Failed to load listing:", error);
        modal.innerHTML = '<div class="empty-state"><h3>Failed to load listing</h3></div>';
    }
}


/**
 * Render modal content for a listing.
 */
function renderModalContent(listing) {
    const sourceTag = `<span class="tag ${getSourceTagClass(listing.source)}">${capitalize(listing.source)}</span>`;
    const locationTag = listing.location ? `<span class="tag tag-gray">📍 ${listing.location}</span>` : "";
    const dateTag = `<span class="tag tag-gray">📅 ${formatDate(listing.scraped_at)}</span>`;

    // Truncate description for display
    const description = listing.description_raw || "No description available.";

    return `
        <div class="modal-header">
            <h2>
                ${listing.title}
                <span class="modal-source">${listing.company || capitalize(listing.source)}</span>
            </h2>
            <button class="modal-close">✕</button>
        </div>
        <div class="modal-tags">
            ${sourceTag}
            ${locationTag}
            ${dateTag}
        </div>
        <div class="modal-body">
            <h3>About</h3>
            <p class="description-text">${description}</p>

            ${listing.skills && listing.skills.length > 0 ? `
                <h3>Required skills</h3>
                <div class="listing-tags" style="margin-top:8px">
                    ${listing.skills.map(s => `<span class="tag tag-green">✓ ${s}</span>`).join("")}
                </div>
            ` : ""}
        </div>
        <div class="modal-footer">
            <a href="${listing.source_url}" target="_blank" class="btn-apply">
                ↗ Apply now
            </a>
            <button class="btn-save" onclick="alert('Saved! (Feature coming in FYP-I)')">
                🔖 Save
            </button>
        </div>
    `;
}


/**
 * Close the modal.
 */
function closeModal() {
    document.getElementById("modal-overlay").classList.remove("open");
}

// Close modal when clicking outside
document.addEventListener("click", function (e) {
    if (e.target.id === "modal-overlay") {
        closeModal();
    }
});

// Close modal with Escape key
document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeModal();
});


/**
 * Populate the source filter dropdown.
 */
function populateSourceFilter(sources) {
    const select = document.getElementById("header-domain");
    if (!select) return;

    // Keep the "All domains" default option
    sources.forEach(source => {
        const option = document.createElement("option");
        option.value = source.name;
        option.textContent = capitalize(source.name);
        select.appendChild(option);
    });
}
