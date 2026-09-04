/**
 * SkillSync — Browse Page Logic
 *
 * Full listing browser with:
 * - Keyword search
 * - Source filter dropdown
 * - Pagination (prev/next)
 * - Listing detail modal
 */

let currentPage = 1;
let currentFilters = {};
const PAGE_SIZE = 12;

document.addEventListener("DOMContentLoaded", async function () {
    await loadBrowseListings();

    // Search input with debounce
    const searchInput = document.getElementById("browse-search");
    if (searchInput) {
        let debounce;
        searchInput.addEventListener("input", function () {
            clearTimeout(debounce);
            debounce = setTimeout(() => {
                currentPage = 1;
                currentFilters.keyword = searchInput.value;
                loadBrowseListings();
            }, 400);
        });
    }

    // Source filter
    const sourceFilter = document.getElementById("browse-source");
    if (sourceFilter) {
        sourceFilter.addEventListener("change", function () {
            currentPage = 1;
            currentFilters.source = sourceFilter.value;
            loadBrowseListings();
        });
    }

    // Tab filters (All / by source)
    document.querySelectorAll(".filter-tab").forEach(tab => {
        tab.addEventListener("click", function () {
            document.querySelectorAll(".filter-tab").forEach(t => t.classList.remove("active"));
            tab.classList.add("active");

            currentPage = 1;
            const filter = tab.dataset.filter;
            if (filter === "all") {
                delete currentFilters.source;
            } else {
                currentFilters.source = filter;
            }
            loadBrowseListings();
        });
    });

    // Populate source dropdown
    try {
        const sources = await fetchSources();
        const select = document.getElementById("browse-source");
        if (select) {
            sources.forEach(s => {
                const option = document.createElement("option");
                option.value = s.name;
                option.textContent = capitalize(s.name) + ` (${s.total_listings})`;
                select.appendChild(option);
            });
        }
    } catch (e) {
        console.error("Failed to load sources for filter:", e);
    }
});


/**
 * Load browse listings with current filters and page.
 */
async function loadBrowseListings() {
    const container = document.getElementById("browse-listings");
    container.innerHTML = '<div class="loading-container"><div class="spinner"></div><p>Loading listings...</p></div>';

    try {
        const data = await fetchListings({
            ...currentFilters,
            page: currentPage,
            page_size: PAGE_SIZE,
        });

        renderBrowseListings(data.listings);
        renderPagination(data);
        document.getElementById("browse-count").textContent =
            `${data.total} opportunit${data.total === 1 ? "y" : "ies"}`;

    } catch (error) {
        console.error("Failed to load listings:", error);
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚠️</div>
                <h3>Could not load listings</h3>
                <p>Make sure the backend API is running at ${API_BASE}</p>
            </div>
        `;
    }
}


/**
 * Render listing cards for the browse page.
 */
function renderBrowseListings(listings) {
    const container = document.getElementById("browse-listings");

    if (!listings || listings.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🔍</div>
                <h3>No listings found</h3>
                <p>Try adjusting your search or filters.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = listings.map(listing => createListingCard(listing)).join("");

    // Click handlers for cards
    container.querySelectorAll(".listing-card").forEach(card => {
        card.addEventListener("click", function () {
            openListingModal(card.dataset.id);
        });
    });
}


/**
 * Render pagination controls.
 */
function renderPagination(data) {
    const container = document.getElementById("pagination");
    if (!container) return;

    const { page, total_pages, total } = data;

    if (total_pages <= 1) {
        container.innerHTML = "";
        return;
    }

    container.innerHTML = `
        <button onclick="goToPage(${page - 1})" ${page <= 1 ? "disabled" : ""}>
            ← Previous
        </button>
        <span class="page-info">Page ${page} of ${total_pages}</span>
        <button onclick="goToPage(${page + 1})" ${page >= total_pages ? "disabled" : ""}>
            Next →
        </button>
    `;
}


/**
 * Navigate to a specific page.
 */
function goToPage(page) {
    currentPage = page;
    loadBrowseListings();
    // Scroll to top of listings
    document.getElementById("browse-listings").scrollIntoView({ behavior: "smooth" });
}
