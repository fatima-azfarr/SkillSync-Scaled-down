/**
 * SkillSync — Sources Page Logic
 *
 * Displays:
 * 1. Source cards (per-platform stats)
 * 2. Scrape status table (last run details)
 * 3. Health check status
 */

document.addEventListener("DOMContentLoaded", async function () {
    await loadSourcesPage();
});


async function loadSourcesPage() {
    try {
        const [sources, statuses, health] = await Promise.all([
            fetchSources(),
            fetchScrapeStatus(),
            fetchHealth(),
        ]);

        renderHealthBanner(health);
        renderSourceCards(sources);
        renderStatusTable(statuses);

    } catch (error) {
        console.error("Failed to load sources page:", error);
        document.getElementById("sources-container").innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚠️</div>
                <h3>Could not connect to API</h3>
                <p>Make sure the backend is running at ${API_BASE}</p>
            </div>
        `;
    }
}


/**
 * Render a health status banner.
 */
function renderHealthBanner(health) {
    const banner = document.getElementById("health-banner");
    if (!banner) return;

    const isHealthy = health.status === "ok";
    banner.innerHTML = `
        <div class="stat-card" style="border-left-color: ${isHealthy ? 'var(--accent)' : '#DC2626'}">
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px">
                <span class="status-badge ${isHealthy ? 'success' : 'failed'}">
                    <span class="dot"></span>
                    ${isHealthy ? 'System Healthy' : 'System Issues'}
                </span>
            </div>
            <div style="font-size:var(--font-sm); color:var(--text-secondary); margin-top:8px">
                Database: <strong>${health.database}</strong> · 
                Last checked: <strong>${timeAgo(health.timestamp)}</strong>
            </div>
        </div>
    `;
}


/**
 * Render source cards.
 */
function renderSourceCards(sources) {
    const container = document.getElementById("sources-container");

    if (!sources || sources.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📭</div>
                <h3>No sources found</h3>
                <p>Scrapers haven't collected any data yet.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = sources.map(source => `
        <div class="source-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px">
                <div class="source-name">${capitalize(source.name)}</div>
                <span class="tag ${getSourceTagClass(source.name)}">${capitalize(source.name)}</span>
            </div>
            <div class="source-count">
                ${source.total_listings} <span>listings</span>
            </div>
            <div class="source-time">
                🕐 Last scraped: ${source.last_scraped ? timeAgo(source.last_scraped) : "Never"}
            </div>
        </div>
    `).join("");
}


/**
 * Render the scrape status table.
 */
function renderStatusTable(statuses) {
    const container = document.getElementById("status-table-container");
    if (!container) return;

    if (!statuses || statuses.length === 0) {
        container.innerHTML = '<p style="padding:20px; color:var(--text-muted)">No scraper runs recorded yet.</p>';
        return;
    }

    container.innerHTML = `
        <table class="status-table">
            <thead>
                <tr>
                    <th>Scraper</th>
                    <th>Status</th>
                    <th>Found</th>
                    <th>New</th>
                    <th>Failed</th>
                    <th>Started</th>
                    <th>Duration</th>
                </tr>
            </thead>
            <tbody>
                ${statuses.map(s => {
                    // Calculate duration
                    let duration = "—";
                    if (s.started_at && s.finished_at) {
                        const diffMs = new Date(s.finished_at) - new Date(s.started_at);
                        const diffSec = Math.floor(diffMs / 1000);
                        duration = diffSec < 60 ? `${diffSec}s` : `${Math.floor(diffSec / 60)}m ${diffSec % 60}s`;
                    }

                    return `
                        <tr>
                            <td>
                                <strong style="text-transform:capitalize">${s.scraper_name}</strong>
                            </td>
                            <td>
                                <span class="status-badge ${s.status === 'success' ? 'success' : s.status === 'failed' ? 'failed' : 'partial'}">
                                    <span class="dot"></span>
                                    ${capitalize(s.status)}
                                </span>
                            </td>
                            <td>${s.listings_found}</td>
                            <td>${s.listings_new}</td>
                            <td>${s.listings_failed}</td>
                            <td>${s.started_at ? timeAgo(s.started_at) : "—"}</td>
                            <td>${duration}</td>
                        </tr>
                    `;
                }).join("")}
            </tbody>
        </table>
    `;
}
