/**
 * SkillSync — Profile & Skills Logic
 *
 * Implements:
 * - Dynamic Profile & Skills management
 * - Interactive Skill Chips & Suggestions
 * - Domain Interest Toggle Chips
 * - Save Profile & Education details
 * - Recompute Recommendations Trigger
 * - Help Tooltip
 * - Authentication & Session Sync
 */

const STUDENT_KEY = "skillsync-student-id";
const STUDENT_NAME_KEY = "skillsync-student-name";

const ALL_SUGGESTIONS = [
    "JavaScript", "Machine Learning", "Docker", "AWS",
    "TensorFlow", "PyTorch", "Java", "C++",
    "Go", "Redis", "Kubernetes", "CUDA"
];

const ALL_DOMAINS = [
    "Web Development", "AI", "NLP", "DevOps",
    "Open Source", "Algorithms", "Product", "Data Science"
];

const DEFAULT_SKILLS = [
    "Python", "React", "TypeScript", "Git",
    "SQL", "NLP", "REST APIs", "CSS",
    "HTML", "Node.js", "Pandas"
];

const DEFAULT_DOMAINS = [
    "Web Development", "AI", "NLP", "Open Source"
];

let currentSkills = [];
let selectedDomains = [];
let currentStudentId = null;

// ─── Session Helpers ──────────────────────────────

function saveSession(studentId, name, email) {
    localStorage.setItem(STUDENT_KEY, studentId);
    if (name) localStorage.setItem(STUDENT_NAME_KEY, name);
    if (email) localStorage.setItem("skillsync-student-email", email);
    localStorage.removeItem("skillsync_guest");
    currentStudentId = studentId;
    document.documentElement.classList.remove("is-guest");
    document.body.classList.remove("is-guest");
    if (typeof updateGlobalNotificationBadges === "function") {
        updateGlobalNotificationBadges();
    }
}

function getSession() {
    return localStorage.getItem(STUDENT_KEY);
}

function clearSession() {
    localStorage.removeItem(STUDENT_KEY);
    localStorage.removeItem(STUDENT_NAME_KEY);
    localStorage.removeItem("skillsync-student-email");
    localStorage.removeItem("skillsync-student-skills");
    localStorage.setItem("skillsync_guest", "true");
    currentStudentId = null;
    document.documentElement.classList.add("is-guest");
    document.body.classList.add("is-guest");
    document.documentElement.classList.add("auth-mode");
    document.body.classList.add("auth-mode");
    if (typeof updateGlobalNotificationBadges === "function") {
        updateGlobalNotificationBadges();
    }
}

// ─── Toast Notifications ──────────────────────────────

let toastTimeout = null;

function showToast(message, type = "success") {
    const toast = document.getElementById("profile-toast");
    if (!toast) return;

    clearTimeout(toastTimeout);
    toast.textContent = message;
    toast.className = `profile-toast ${type}`;
    toast.style.display = "block";

    toastTimeout = setTimeout(() => {
        toast.style.display = "none";
    }, 4000);
}

function showAuthMessage(text, type = "error") {
    const container = document.getElementById("auth-message");
    if (!container) return;
    const cssClass = type === "error" ? "form-error" : "form-success";
    const icon = type === "error"
        ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`
        : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`;
    container.innerHTML = `<div class="${cssClass}">${icon}<span>${escapeHtml(text)}</span></div>`;
}

// ─── Tab Switching (Login / Register) ──────────────────────────────

function switchTab(tab) {
    const loginForm = document.getElementById("login-form");
    const registerForm = document.getElementById("register-form");
    const loginTab = document.getElementById("tab-login");
    const registerTab = document.getElementById("tab-register");
    const msg = document.getElementById("auth-message");
    if (msg) msg.innerHTML = "";
    document.querySelectorAll(".form-input.is-invalid").forEach(el => el.classList.remove("is-invalid"));

    if (tab === "login") {
        loginForm.style.display = "block";
        registerForm.style.display = "none";
        loginTab.classList.add("active");
        registerTab.classList.remove("active");
    } else {
        loginForm.style.display = "none";
        registerForm.style.display = "block";
        loginTab.classList.remove("active");
        registerTab.classList.add("active");
    }
}

// ─── Views Switching ──────────────────────────────

function showAuthView() {
    document.documentElement.classList.add("auth-mode");
    document.body.classList.add("auth-mode");

    const authView = document.getElementById("auth-view");
    const profileView = document.getElementById("profile-view");
    const sidebar = document.getElementById("app-sidebar") || document.querySelector(".sidebar");

    if (authView) authView.style.display = "block";
    if (profileView) profileView.style.display = "none";
    if (sidebar) sidebar.style.display = "none";
}

function showProfileView(student) {
    document.documentElement.classList.remove("auth-mode");
    document.body.classList.remove("auth-mode");

    const authView = document.getElementById("auth-view");
    const profileView = document.getElementById("profile-view");
    const sidebar = document.getElementById("app-sidebar") || document.querySelector(".sidebar");

    if (authView) authView.style.display = "none";
    if (profileView) profileView.style.display = "flex";
    if (sidebar) sidebar.style.display = "flex";

    // User details in Card 1
    const name = student.name || "Fatima";
    const email = student.email || "fa23-bcs-185@cuilahore.edu.pk";
    const initials = name
        .split(" ")
        .map((w) => w[0])
        .join("")
        .toUpperCase()
        .slice(0, 2) || "F";

    document.getElementById("profile-card-name").textContent = name;
    document.getElementById("profile-card-email").textContent = email;
    document.getElementById("profile-card-avatar").textContent = initials;

    // Sidebar User Badge
    const sidebarName = document.getElementById("sidebar-user-name");
    const sidebarAvatar = document.getElementById("sidebar-user-avatar");
    const sidebarEmail = document.getElementById("sidebar-user-email");
    if (sidebarName) sidebarName.textContent = name.split(" ")[0];
    if (sidebarAvatar) sidebarAvatar.textContent = initials;
    if (sidebarEmail) sidebarEmail.textContent = email;

    // Education inputs
    document.getElementById("profile-university").value =
        student.university || "NUST — National University of Sciences and Technology";
    document.getElementById("profile-field").value =
        student.field_of_study || "Computer Science";

    // Skills
    if (student.skills && student.skills.length > 0) {
        currentSkills = [...student.skills];
    } else {
        currentSkills = [...DEFAULT_SKILLS];
    }

    // Domain interests
    if (student.domain_interests && student.domain_interests.length > 0) {
        selectedDomains = [...student.domain_interests];
    } else {
        selectedDomains = [...DEFAULT_DOMAINS];
    }

    renderSkillChips();
    renderSuggestions();
    renderDomainChips();

    try {
        localStorage.setItem("skillsync-student-skills", JSON.stringify(currentSkills));
    } catch (e) {}
}

// ─── Skills Rendering & Interaction ──────────────────────────────

function renderSkillChips() {
    const container = document.getElementById("skills-list");
    if (!container) return;

    if (currentSkills.length === 0) {
        container.innerHTML = '<span style="color:var(--text-muted);font-size:0.85rem;font-style:italic;">No skills added yet.</span>';
        return;
    }

    container.innerHTML = currentSkills
        .map(
            (skill, i) => `
        <span class="modern-skill-pill">
            ${escapeHtml(skill)}
            <span class="remove-x" onclick="removeSkill(${i})" title="Remove skill">×</span>
        </span>
    `
        )
        .join("");
}

function renderSuggestions() {
    const container = document.getElementById("suggestions-list");
    if (!container) return;

    // Filter suggestions that are not already in currentSkills
    const available = ALL_SUGGESTIONS.filter(
        (s) => !currentSkills.some((cs) => cs.toLowerCase() === s.toLowerCase())
    );

    if (available.length === 0) {
        container.innerHTML = '<span style="color:var(--text-muted);font-size:0.8rem;">All suggestions added!</span>';
        return;
    }

    container.innerHTML = available
        .map(
            (s) => `
        <span class="suggestion-pill" onclick="addSkill('${escapeHtml(s)}')">
            + ${escapeHtml(s)}
        </span>
    `
        )
        .join("");
}

function addSkill(skillName) {
    const clean = skillName.trim();
    if (!clean) return;

    const exists = currentSkills.some((s) => s.toLowerCase() === clean.toLowerCase());
    if (!exists) {
        currentSkills.push(clean);
        renderSkillChips();
        renderSuggestions();
    }
}

function removeSkill(index) {
    currentSkills.splice(index, 1);
    renderSkillChips();
    renderSuggestions();
}

function addSkillFromInput() {
    const input = document.getElementById("skill-input");
    if (!input) return;
    const value = input.value.trim();
    if (value) {
        addSkill(value);
        input.value = "";
    }
}

// ─── Domain Interests Rendering & Toggle ──────────────────────────────

function renderDomainChips() {
    const container = document.getElementById("domains-list");
    if (!container) return;

    container.innerHTML = ALL_DOMAINS.map((domain) => {
        const isSelected = selectedDomains.includes(domain);
        const cssClass = isSelected ? "domain-pill selected" : "domain-pill unselected";
        return `
            <span class="${cssClass}" onclick="toggleDomain('${escapeHtml(domain)}')">
                ${escapeHtml(domain)}
            </span>
        `;
    }).join("");
}

function toggleDomain(domain) {
    const index = selectedDomains.indexOf(domain);
    if (index > -1) {
        selectedDomains.splice(index, 1);
    } else {
        selectedDomains.push(domain);
    }
    renderDomainChips();
}

// ─── Save Changes ──────────────────────────────

async function handleSaveChanges() {
    const studentId = getSession();
    const saveBtn = document.getElementById("save-changes-btn");

    if (!studentId) {
        showToast("Please log in to save changes.", "error");
        return;
    }

    saveBtn.disabled = true;
    saveBtn.textContent = "Saving...";

    try {
        const university = document.getElementById("profile-university").value.trim() || null;
        const fieldOfStudy = document.getElementById("profile-field").value.trim() || null;
        const preferredDomain = selectedDomains[0] || null;

        await updateStudentProfile(studentId, {
            skills: currentSkills,
            preferred_domain: preferredDomain,
            preferred_location: null,
            university: university,
            field_of_study: fieldOfStudy,
            domain_interests: selectedDomains,
        });

        showToast("Profile & skills saved successfully!");
        try {
            localStorage.setItem("skillsync-student-skills", JSON.stringify(currentSkills));
        } catch (e) {}
    } catch (err) {
        showToast(err.message, "error");
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = "Save changes";
    }
}

// ─── Recompute Recommendations & Results Modal ──────────────────────────────

function openRecomputeModal(data) {
    const modal = document.getElementById("recompute-modal");
    if (!modal) return;

    const stats = data?.stats || {};
    const totalEvaluated = stats.total_evaluated ?? 0;
    const matchedCount = stats.matched_count ?? (data?.top_matches?.length || 0);
    const nearMissCount = stats.near_miss_count ?? (data?.top_near_misses?.length || 0);

    // Populate stat counters
    const evalEl = document.getElementById("recompute-stat-evaluated");
    const matchEl = document.getElementById("recompute-stat-matched");
    const nearEl = document.getElementById("recompute-stat-nearmiss");
    const matchCountBadge = document.getElementById("recompute-matches-count");
    const nearCountBadge = document.getElementById("recompute-nearmiss-count");

    if (evalEl) evalEl.textContent = totalEvaluated;
    if (matchEl) matchEl.textContent = matchedCount;
    if (nearEl) nearEl.textContent = nearMissCount;
    if (matchCountBadge) matchCountBadge.textContent = `${matchedCount} found`;
    if (nearCountBadge) nearCountBadge.textContent = `${nearMissCount} found`;

    // Render Top Matches List
    const matchesList = document.getElementById("recompute-matches-list");
    if (matchesList) {
        const matches = data?.top_matches || [];
        if (matches.length === 0) {
            matchesList.innerHTML = `
                <div class="empty-results-notice">
                    No opportunities with ≥70% skill match found yet. Try adding relevant skills or check the near misses below!
                </div>
            `;
        } else {
            matchesList.innerHTML = matches.map((item) => {
                const matchedChips = (item.matched_skills || [])
                    .map((s) => `<span class="matched-pill">✓ ${escapeHtml(s)}</span>`)
                    .join("");
                return `
                    <div class="recompute-opp-card">
                        <div class="opp-card-top">
                            <div class="opp-card-info">
                                <h4>${escapeHtml(item.title)}</h4>
                                <div class="opp-card-meta">
                                    <span>${escapeHtml(item.company)}</span>
                                    <span class="opp-source-tag">${escapeHtml(item.source)}</span>
                                </div>
                            </div>
                            <span class="opp-score-badge score-badge-high">${item.match_score}% Match</span>
                        </div>
                        <div class="opp-skills-block">
                            <div class="skills-row-wrap">
                                ${matchedChips}
                            </div>
                        </div>
                    </div>
                `;
            }).join("");
        }
    }

    // Render Near Misses List
    const nearList = document.getElementById("recompute-nearmiss-list");
    if (nearList) {
        const nearMisses = data?.top_near_misses || [];
        if (nearMisses.length === 0) {
            nearList.innerHTML = `
                <div class="empty-results-notice">
                    No near misses found in the 40–69% range.
                </div>
            `;
        } else {
            nearList.innerHTML = nearMisses.map((item) => {
                const matchedChips = (item.matched_skills || [])
                    .map((s) => `<span class="matched-pill">✓ ${escapeHtml(s)}</span>`)
                    .join("");
                const missingChips = (item.missing_skills || [])
                    .map((s) => `<span class="missing-pill">+ Missing: ${escapeHtml(s)}</span>`)
                    .join("");
                return `
                    <div class="recompute-opp-card">
                        <div class="opp-card-top">
                            <div class="opp-card-info">
                                <h4>${escapeHtml(item.title)}</h4>
                                <div class="opp-card-meta">
                                    <span>${escapeHtml(item.company)}</span>
                                    <span class="opp-source-tag">${escapeHtml(item.source)}</span>
                                </div>
                            </div>
                            <span class="opp-score-badge score-badge-mid">${item.match_score}% Match</span>
                        </div>
                        <div class="opp-skills-block">
                            <div class="skills-row-wrap">
                                ${matchedChips}
                                ${missingChips}
                            </div>
                        </div>
                    </div>
                `;
            }).join("");
        }
    }

    modal.style.display = "flex";
    modal.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
}

function closeRecomputeModal() {
    const modal = document.getElementById("recompute-modal");
    if (!modal) return;
    modal.style.display = "none";
    modal.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
}

const RECOMPUTE_ICON_SVG = `<svg id="recompute-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>`;
const RECOMPUTE_SPIN_SVG = `<svg class="spin-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>`;

async function handleRecompute() {
    const studentId = getSession();
    const btn = document.getElementById("recompute-btn");

    btn.disabled = true;
    btn.innerHTML = `${RECOMPUTE_SPIN_SVG} <span>Recomputing...</span>`;

    try {
        if (studentId) {
            // Auto-save latest skills first so recomputation reflects all current profile edits
            const university = document.getElementById("profile-university")?.value?.trim() || null;
            const fieldOfStudy = document.getElementById("profile-field")?.value?.trim() || null;
            const preferredDomain = selectedDomains[0] || null;

            try {
                await updateStudentProfile(studentId, {
                    skills: currentSkills,
                    preferred_domain: preferredDomain,
                    preferred_location: null,
                    university: university,
                    field_of_study: fieldOfStudy,
                    domain_interests: selectedDomains,
                });
            } catch (saveErr) {
                console.warn("Auto-save before recompute failed:", saveErr);
            }

            const result = await recomputeRecommendations(studentId);
            openRecomputeModal(result);
            showToast("Recommendations updated based on your latest skills!");
        } else {
            showToast("Please sign in or register to recompute recommendations.", "error");
        }
    } catch (err) {
        showToast(err.message || "Could not recompute recommendations", "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `${RECOMPUTE_ICON_SVG} <span>Recompute</span>`;
    }
}

// ─── Floating Help Button ──────────────────────────────

function toggleHelpPopup() {
    const popup = document.getElementById("help-popup");
    if (popup) {
        popup.classList.toggle("open");
    }
}

// Close help on outside click
document.addEventListener("click", (e) => {
    const helpBtn = document.getElementById("help-btn");
    const helpPopup = document.getElementById("help-popup");
    if (helpPopup && helpPopup.classList.contains("open")) {
        if (!helpPopup.contains(e.target) && e.target !== helpBtn) {
            helpPopup.classList.remove("open");
        }
    }
});

// ─── Init & Authentication Flow ──────────────────────────────

async function loadCurrentStudent() {
    let studentId = getSession();

    if (!studentId) {
        try {
            const current = await safeFetch(`${API_BASE}/students/current`);
            if (current && current.id) {
                saveSession(current.id, current.name, current.email);
                showProfileView(current);
                return;
            }
        } catch (e) {}
        showAuthView();
        return;
    }

    try {
        const student = await fetchStudent(studentId);
        showProfileView(student);
    } catch (err) {
        if (err.status === 404 || err.message?.toLowerCase().includes("not found")) {
            clearSession();
            showAuthView();
        } else {
            // In case of connection issue, load cached session view
            showProfileView({
                name: localStorage.getItem(STUDENT_NAME_KEY) || "Fatima",
                email: localStorage.getItem("skillsync-student-email") || "fa23-bcs-185@cuilahore.edu.pk",
                university: "Comsats University",
                field_of_study: "Computer Science",
                skills: DEFAULT_SKILLS,
                domain_interests: DEFAULT_DOMAINS,
            });
        }
    }
}

// ─── Event Listeners ──────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    // Add skill input Enter key
    const skillInput = document.getElementById("skill-input");
    if (skillInput) {
        skillInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                addSkillFromInput();
            }
        });
    }

    // Add skill button
    document.getElementById("skill-add-btn")?.addEventListener("click", addSkillFromInput);

    // Save changes button
    document.getElementById("save-changes-btn")?.addEventListener("click", handleSaveChanges);

    // Recompute button
    document.getElementById("recompute-btn")?.addEventListener("click", handleRecompute);

    // Recompute Modal Close Listeners
    document.getElementById("recompute-modal-close")?.addEventListener("click", closeRecomputeModal);
    document.getElementById("recompute-modal-done")?.addEventListener("click", closeRecomputeModal);
    document.getElementById("recompute-modal")?.addEventListener("click", (e) => {
        if (e.target.id === "recompute-modal") {
            closeRecomputeModal();
        }
    });
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            closeRecomputeModal();
        }
    });

    // Floating help button
    document.getElementById("help-btn")?.addEventListener("click", (e) => {
        e.stopPropagation();
        toggleHelpPopup();
    });

    // Login Form Submit
    document.getElementById("login-form")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const submitBtn = document.getElementById("login-submit");
        submitBtn.disabled = true;
        submitBtn.textContent = "Logging in...";

        try {
            const email = document.getElementById("login-email").value;
            const password = document.getElementById("login-password").value;
            const student = await loginStudent(email, password);
            saveSession(student.id, student.name, student.email);
            showProfileView(student);
        } catch (err) {
            showAuthMessage(err.message, "error");
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = "Log In";
        }
    });

    // Register Form Submit
    document.getElementById("register-form")?.addEventListener("submit", async (e) => {
        e.preventDefault();

        // Clear previous messages and invalid styling
        const authMsg = document.getElementById("auth-message");
        if (authMsg) authMsg.innerHTML = "";
        document.querySelectorAll("#register-form .form-input.is-invalid").forEach(el => el.classList.remove("is-invalid"));

        const firstNameInput = document.getElementById("register-firstname");
        const lastNameInput = document.getElementById("register-lastname");
        const emailInput = document.getElementById("register-email");
        const passwordInput = document.getElementById("register-password");
        const confirmPasswordInput = document.getElementById("register-confirm-password");

        const firstName = firstNameInput?.value.trim() || "";
        const lastName = lastNameInput?.value.trim() || "";
        const email = emailInput?.value.trim() || "";
        const password = passwordInput?.value || "";
        const confirmPassword = confirmPasswordInput?.value || "";

        // 1. Compulsory Validation: First Name
        if (!firstName) {
            firstNameInput?.classList.add("is-invalid");
            showAuthMessage("First name is compulsory. Please enter your first name.", "error");
            firstNameInput?.focus();
            return;
        }

        // 2. Compulsory Validation: Last Name
        if (!lastName) {
            lastNameInput?.classList.add("is-invalid");
            showAuthMessage("Last name is compulsory. Please enter your last name.", "error");
            lastNameInput?.focus();
            return;
        }

        // 3. Compulsory Validation: Email
        if (!email) {
            emailInput?.classList.add("is-invalid");
            showAuthMessage("Email is compulsory. Please enter your email address.", "error");
            emailInput?.focus();
            return;
        }
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            emailInput?.classList.add("is-invalid");
            showAuthMessage("Please enter a valid email address.", "error");
            emailInput?.focus();
            return;
        }

        // 4. Compulsory Validation: Password
        if (!password) {
            passwordInput?.classList.add("is-invalid");
            showAuthMessage("Password is compulsory. Please enter a password.", "error");
            passwordInput?.focus();
            return;
        }
        if (password.length < 8) {
            passwordInput?.classList.add("is-invalid");
            showAuthMessage("Password must be at least 8 characters long.", "error");
            passwordInput?.focus();
            return;
        }

        // 5. Compulsory Validation: Re-enter Password
        if (!confirmPassword) {
            confirmPasswordInput?.classList.add("is-invalid");
            showAuthMessage("Please re-enter your password to confirm.", "error");
            confirmPasswordInput?.focus();
            return;
        }
        if (password !== confirmPassword) {
            confirmPasswordInput?.classList.add("is-invalid");
            showAuthMessage("Passwords do not match. Please verify and re-enter identical passwords.", "error");
            confirmPasswordInput?.focus();
            return;
        }

        const submitBtn = document.getElementById("register-submit");
        submitBtn.disabled = true;
        submitBtn.textContent = "Creating account...";

        try {
            const fullName = `${firstName} ${lastName}`.trim();
            const data = {
                name: fullName,
                first_name: firstName,
                last_name: lastName,
                email: email,
                password: password,
                skills: DEFAULT_SKILLS,
                university: "NUST — National University of Sciences and Technology",
                field_of_study: "Computer Science",
                domain_interests: DEFAULT_DOMAINS,
            };

            const student = await registerStudent(data);
            saveSession(student.id, student.name, student.email);
            showProfileView(student);
        } catch (err) {
            showAuthMessage(err.message, "error");
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = "Create Account";
        }
    });

    // Clear is-invalid styling as user types into any register field
    ["register-firstname", "register-lastname", "register-email", "register-password", "register-confirm-password"].forEach(id => {
        const el = document.getElementById(id);
        el?.addEventListener("input", () => {
            el.classList.remove("is-invalid");
            const authMsg = document.getElementById("auth-message");
            if (authMsg && authMsg.querySelector(".form-error")) {
                authMsg.innerHTML = "";
            }
        });
    });

    // Sidebar sign out button
    document.getElementById("sidebar-logout-btn")?.addEventListener("click", (e) => {
        e.preventDefault();
        clearSession();
        showAuthView();
    });

    // Explore as guest link
    document.getElementById("auth-guest-link")?.addEventListener("click", () => {
        clearSession();
    });

    loadCurrentStudent();
});

// Helper to escape HTML characters
function escapeHtml(str) {
    if (!str) return "";
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}