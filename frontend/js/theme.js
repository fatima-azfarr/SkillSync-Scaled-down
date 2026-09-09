/**
 * SkillSync — Theme / Dark Mode Toggle
 * 
 * Handles light/dark mode switching:
 * - Reads saved preference from localStorage
 * - Applies theme on page load
 * - Toggles theme when user clicks the dark mode button
 */

(function() {
    const THEME_KEY = "skillsync-theme";

    const MOON_ICON = `<svg class="theme-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`;
    const SUN_ICON = `<svg class="theme-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`;

    /**
     * Apply the given theme to the page.
     * @param {string} theme - "light" or "dark"
     */
    function applyTheme(theme) {
        document.documentElement.setAttribute("data-theme", theme);
        
        // Update toggle button icon and text
        const toggleBtn = document.getElementById("theme-toggle");
        if (toggleBtn) {
            toggleBtn.innerHTML = theme === "dark"
                ? `${SUN_ICON}<span>Light mode</span>`
                : `${MOON_ICON}<span>Dark mode</span>`;
        }
        // Update auth screen toggle button if present
        const authToggleBtn = document.getElementById("auth-theme-toggle");
        if (authToggleBtn) {
            authToggleBtn.innerHTML = theme === "dark"
                ? `<svg class="theme-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`
                : `<svg class="theme-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`;
        }
    }

    /**
     * Get the saved theme or default to "light".
     */
    function getSavedTheme() {
        return localStorage.getItem(THEME_KEY) || "light";
    }

    /**
     * Toggle between light and dark mode.
     */
    function toggleTheme() {
        const current = getSavedTheme();
        const next = current === "dark" ? "light" : "dark";
        localStorage.setItem(THEME_KEY, next);
        applyTheme(next);
    }

    // Apply saved theme immediately on load
    applyTheme(getSavedTheme());

    // Set up click handler once DOM is ready
    document.addEventListener("DOMContentLoaded", function() {
        // Re-apply to make sure button text is updated
        applyTheme(getSavedTheme());

        const toggleBtn = document.getElementById("theme-toggle");
        if (toggleBtn) {
            toggleBtn.addEventListener("click", toggleTheme);
        }

        const authToggleBtn = document.getElementById("auth-theme-toggle");
        if (authToggleBtn) {
            authToggleBtn.addEventListener("click", toggleTheme);
        }
    });
})();
