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

    /**
     * Apply the given theme to the page.
     * @param {string} theme - "light" or "dark"
     */
    function applyTheme(theme) {
        document.documentElement.setAttribute("data-theme", theme);
        
        // Update toggle button text
        const toggleBtn = document.getElementById("theme-toggle");
        if (toggleBtn) {
            toggleBtn.innerHTML = theme === "dark"
                ? '☀️ <span>Light mode</span>'
                : '🌙 <span>Dark mode</span>';
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
    });
})();
