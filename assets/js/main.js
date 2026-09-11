// Navbar
(() => {
    'use strict';

    const navbar = document.getElementById('navbar');
    const scrollThreshold = 40;

    /* ---------- Sticky: Transparent over hero -> Solid on scroll ---------- */
    const handleScroll = () => {
        const scrolled = window.scrollY > scrollThreshold;
        navbar.classList.toggle('navbar-scrolled', scrolled);
        navbar.classList.toggle('navbar-transparent', !scrolled);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();

    /* ---------- Expandable Search Panel ---------- */
    const searchToggle = document.getElementById('navbar-search-toggle');
    const searchPanel = document.getElementById('navbar-search-panel');
    const searchClose = document.getElementById('navbar-search-close');

    const toggleSearch = (open) => {
        searchPanel.classList.toggle('hidden', !open);
        searchToggle.setAttribute('aria-expanded', String(open));
        if (open) {
            const input = searchPanel.querySelector('input');
            if (input) setTimeout(() => input.focus(), 50);
        }
    };
    searchToggle?.addEventListener('click', () => {
        toggleSearch(searchPanel.classList.contains('hidden'));
    });
    searchClose?.addEventListener('click', () => toggleSearch(false));

    /* ---------- Mobile Drawer ---------- */
    const menuToggle = document.getElementById('mobile-menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    const menuClose = document.getElementById('mobile-menu-close');
    const menuBackdrop = document.getElementById('mobile-menu-backdrop');

    const openDrawer = () => {
        mobileMenu.classList.remove('hidden');
        menuToggle.setAttribute('aria-expanded', 'true');
        document.body.classList.add('no-scroll');
        menuClose.focus();
    };
    const closeDrawer = () => {
        mobileMenu.classList.add('hidden');
        menuToggle.setAttribute('aria-expanded', 'false');
        document.body.classList.remove('no-scroll');
        menuToggle.focus();
    };

    menuToggle?.addEventListener('click', openDrawer);
    menuClose?.addEventListener('click', closeDrawer);
    menuBackdrop?.addEventListener('click', closeDrawer);

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (!mobileMenu.classList.contains('hidden')) closeDrawer();
            if (!searchPanel.classList.contains('hidden')) toggleSearch(false);
        }
    });

    /* ---------- Auth State Demo Toggle (integration point for Django) ---------- */
    // Set window.isAuthenticated = true (before this script runs) to preview logged-in state.
    const guestBlock = document.getElementById('navbar-auth-guest');
    const userBlock = document.getElementById('navbar-auth-user');
    if (window.isAuthenticated) {
        guestBlock?.classList.add('hidden');
        userBlock?.classList.remove('hidden');
    }
})();

const navbar = document.getElementById('navbar');
const logo = document.getElementById('navbar-logo');

const handleScroll = () => {
    const scrolled = window.scrollY > 40;

    navbar.classList.toggle('navbar-scrolled', scrolled);
    navbar.classList.toggle('navbar-transparent', !scrolled);

    logo.classList.toggle('brightness-0', !scrolled);
    logo.classList.toggle('invert', !scrolled);
};

window.addEventListener('scroll', handleScroll);
handleScroll();

// announcement-bar
(() => {
    "use strict";
    const bar = document.getElementById("announcement-bar");
    const closeBtn = document.getElementById("announcement-close");
    if (!bar || !closeBtn) return;

    closeBtn.addEventListener("click", () => {
        bar.style.transition = "opacity 200ms ease, max-height 200ms ease";
        bar.style.opacity = "0";
        bar.style.maxHeight = bar.offsetHeight + "px";
        requestAnimationFrame(() => {
            bar.style.maxHeight = "0px";
            bar.style.overflow = "hidden";
        });
        setTimeout(() => bar.remove(), 200);
    });
})();

(() => {
    "use strict";

    const widget = document.getElementById("travel-search-widget");
    if (!widget) return;

    const MONTH_NAMES = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ];
    const WEEKDAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

    /* =========================================================
    TAB SWITCHING
    ========================================================= */
    const tabs = widget.querySelectorAll(".tsw-tab");
    const panels = widget.querySelectorAll(".tsw-panel");

    tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            const target = tab.getAttribute("data-tab");
            tabs.forEach((t) => {
                t.classList.remove("is-active");
                t.setAttribute("aria-selected", "false");
            });
            tab.classList.add("is-active");
            tab.setAttribute("aria-selected", "true");
            panels.forEach((panel) => panel.classList.toggle("hidden", panel.getAttribute("data-panel") !== target));
        });

        // Keyboard navigation between tabs
        tab.addEventListener("keydown", (e) => {
            const tabArray = Array.from(tabs);
            const index = tabArray.indexOf(tab);
            if (e.key === "ArrowRight") tabArray[(index + 1) % tabArray.length].focus();
            if (e.key === "ArrowLeft") tabArray[(index - 1 + tabArray.length) % tabArray.length].focus();
        });
    });

    /* =========================================================
    SWAP FROM / TO
    ========================================================= */
    const swapBtn = document.getElementById("tsw-swap");
    const fromInput = document.getElementById("tsw-from");
    const toInput = document.getElementById("tsw-to");

    swapBtn?.addEventListener("click", () => {
        const temp = fromInput.value;
        fromInput.value = toInput.value;
        toInput.value = temp;
    });

    /* =========================================================
    CUSTOM DATE PICKER
    ========================================================= */
    function closeAllDatepickers(except) {
        widget.querySelectorAll(".tsw-datepicker").forEach((dp) => {
            if (dp !== except) dp.classList.add("hidden");
        });
        widget.querySelectorAll(".tsw-date-trigger").forEach((btn) => btn.setAttribute("aria-expanded", "false"));
    }

    function buildCalendar(container, triggerBtn) {
        let viewDate = new Date();
        let selectedDate = null;

        function render() {
            const year = viewDate.getFullYear();
            const month = viewDate.getMonth();
            const firstDay = new Date(year, month, 1).getDay();
            const daysInMonth = new Date(year, month + 1, 0).getDate();
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            let html = `
            <div class="tsw-cal-header">
                <button type="button" class="tsw-cal-nav" data-nav="prev" aria-label="Previous month"><i class="fa-solid fa-chevron-left"></i></button>
                <span class="tsw-cal-title">${MONTH_NAMES[month]} ${year}</span>
                <button type="button" class="tsw-cal-nav" data-nav="next" aria-label="Next month"><i class="fa-solid fa-chevron-right"></i></button>
            </div>
            <div class="tsw-cal-grid">
                ${WEEKDAYS.map((d) => `<span class="tsw-cal-weekday">${d}</span>`).join("")}
        `;

            for (let i = 0; i < firstDay; i++) {
                html += `<span class="tsw-cal-day is-empty"></span>`;
            }

            for (let day = 1; day <= daysInMonth; day++) {
                const cellDate = new Date(year, month, day);
                const isPast = cellDate < today;
                const isToday = cellDate.getTime() === today.getTime();
                const isSelected = selectedDate && cellDate.getTime() === selectedDate.getTime();
                html += `<button type="button"
                        class="tsw-cal-day ${isPast ? "is-disabled" : ""} ${isToday ? "is-today" : ""} ${isSelected ? "is-selected" : ""}"
                        ${isPast ? "disabled" : ""}
                        data-day="${day}"
                        aria-label="${MONTH_NAMES[month]} ${day}, ${year}">${day}</button>`;
            }

            html += `</div>`;
            container.innerHTML = html;

            container.querySelector('[data-nav="prev"]').addEventListener("click", () => {
                viewDate = new Date(year, month - 1, 1);
                render();
            });
            container.querySelector('[data-nav="next"]').addEventListener("click", () => {
                viewDate = new Date(year, month + 1, 1);
                render();
            });
            container.querySelectorAll(".tsw-cal-day[data-day]").forEach((dayBtn) => {
                dayBtn.addEventListener("click", () => {
                    const day = parseInt(dayBtn.getAttribute("data-day"), 10);
                    selectedDate = new Date(year, month, day);
                    const label = triggerBtn.querySelector("[data-date-label]");
                    if (label) {
                        label.textContent = selectedDate.toLocaleDateString("en-US", {
                            day: "numeric",
                            month: "short",
                            year: "numeric",
                        });
                    }
                    triggerBtn.closest(".tsw-field")?.classList.remove("tsw-field-invalid");
                    const errorEl = document.getElementById(`tsw-error-${triggerBtn.id.replace("tsw-", "")}`);
                    errorEl?.classList.add("hidden");
                    container.classList.add("hidden");
                    triggerBtn.setAttribute("aria-expanded", "false");
                });
            });
        }

        render();
    }

    widget.querySelectorAll(".tsw-date-trigger").forEach((triggerBtn) => {
        const targetId = triggerBtn.id;
        const dp = widget.querySelector(`.tsw-datepicker[data-datepicker-for="${targetId}"]`);
        if (!dp) return;

        let built = false;
        triggerBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            const isHidden = dp.classList.contains("hidden");
            closeAllDatepickers(dp);
            if (isHidden) {
                if (!built) {
                    buildCalendar(dp, triggerBtn);
                    built = true;
                }
                dp.classList.remove("hidden");
                triggerBtn.setAttribute("aria-expanded", "true");
            } else {
                dp.classList.add("hidden");
                triggerBtn.setAttribute("aria-expanded", "false");
            }
        });
    });

    /* =========================================================
    TRAVELLER SELECTOR + CABIN CLASS
    ========================================================= */
    const travellerTrigger = document.getElementById("tsw-traveller-trigger");
    const travellerPanel = document.getElementById("tsw-traveller-panel");
    const travellerSummary = document.getElementById("tsw-traveller-summary");
    let cabinClass = "Economy";

    travellerTrigger?.addEventListener("click", (e) => {
        e.stopPropagation();
        const isHidden = travellerPanel.classList.contains("hidden");
        closeAllDatepickers(travellerPanel);
        travellerPanel.classList.toggle("hidden", !isHidden ? true : false);
        if (isHidden) {
            travellerPanel.classList.remove("hidden");
            travellerTrigger.setAttribute("aria-expanded", "true");
        }
    });

    widget.querySelectorAll(".tsw-counter").forEach((counter) => {
        const min = parseInt(counter.getAttribute("data-min"), 10);
        const max = parseInt(counter.getAttribute("data-max"), 10);
        const valueEl = counter.querySelector("[data-value]");
        const decBtn = counter.querySelector('[data-action="decrement"]');
        const incBtn = counter.querySelector('[data-action="increment"]');

        function update(val) {
            valueEl.textContent = val;
            decBtn.disabled = val <= min;
            incBtn.disabled = val >= max;
        }

        decBtn.addEventListener("click", () => {
            let val = parseInt(valueEl.textContent, 10);
            if (val > min) update(val - 1);
        });
        incBtn.addEventListener("click", () => {
            let val = parseInt(valueEl.textContent, 10);
            if (val < max) update(val + 1);
        });

        update(parseInt(valueEl.textContent, 10));
    });

    widget.querySelectorAll(".tsw-class-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            widget.querySelectorAll(".tsw-class-btn").forEach((b) => {
                b.classList.remove("is-active");
                b.setAttribute("aria-checked", "false");
            });
            btn.classList.add("is-active");
            btn.setAttribute("aria-checked", "true");
            cabinClass = btn.getAttribute("data-class");
        });
    });

    document.getElementById("tsw-traveller-apply")?.addEventListener("click", () => {
        const adults = widget.querySelector('[data-counter="adults"] [data-value]').textContent;
        const children = widget.querySelector('[data-counter="children"] [data-value]').textContent;
        const infants = widget.querySelector('[data-counter="infants"] [data-value]').textContent;

        let summary = `${adults} Adult${adults > 1 ? "s" : ""}`;
        if (children !== "0") summary += `, ${children} Child${children > 1 ? "ren" : ""}`;
        if (infants !== "0") summary += `, ${infants} Infant${infants > 1 ? "s" : ""}`;
        summary += `, ${cabinClass}`;

        travellerSummary.textContent = summary;
        travellerPanel.classList.add("hidden");
        travellerTrigger.setAttribute("aria-expanded", "false");
    });

    /* =========================================================
    CLOSE DROPDOWNS ON OUTSIDE CLICK / ESC
    ========================================================= */
    document.addEventListener("click", () => {
        closeAllDatepickers(null);
        travellerPanel?.classList.add("hidden");
        travellerTrigger?.setAttribute("aria-expanded", "false");
    });
    widget.addEventListener("click", (e) => e.stopPropagation());
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            closeAllDatepickers(null);
            travellerPanel?.classList.add("hidden");
            travellerTrigger?.setAttribute("aria-expanded", "false");
        }
    });

    /* =========================================================
    VALIDATION PLACEHOLDERS
    ========================================================= */
    function validateActivePanel() {
        let isValid = true;
        const activePanel = widget.querySelector(".tsw-panel:not(.hidden)");
        if (!activePanel) return true;

        const requiredInputs = activePanel.querySelectorAll("[required]");
        requiredInputs.forEach((input) => {
            const field = input.closest(".tsw-field");
            if (!input.value || !input.value.trim()) {
                isValid = false;
                field?.classList.add("tsw-field-invalid", "tsw-shake");
                setTimeout(() => field?.classList.remove("tsw-shake"), 400);
                const errorEl = document.getElementById(`tsw-error-${input.id.replace("tsw-", "")}`);
                errorEl?.classList.remove("hidden");
            } else {
                field?.classList.remove("tsw-field-invalid");
            }
        });

        // Flights panel: departure date required (custom button, not native input)
        if (activePanel.getAttribute("data-panel") === "flights") {
            const departureBtn = document.getElementById("tsw-departure");
            const label = departureBtn?.querySelector("[data-date-label]");
            if (label && label.textContent === "Select date") {
                isValid = false;
                departureBtn.closest(".tsw-field")?.classList.add("tsw-field-invalid", "tsw-shake");
                setTimeout(() => departureBtn.closest(".tsw-field")?.classList.remove("tsw-shake"), 400);
                document.getElementById("tsw-error-departure")?.classList.remove("hidden");
            }
        }

        return isValid;
    }

    /* =========================================================
    RECENT SEARCHES (persisted locally for this project)
    ========================================================= */
    const RECENT_KEY = "tsw_recent_searches";
    const recentWrapper = document.getElementById("tsw-recent-wrapper");
    const recentList = document.getElementById("tsw-recent-list");

    function getRecentSearches() {
        try {
            return JSON.parse(localStorage.getItem(RECENT_KEY)) || [];
        } catch (err) {
            return [];
        }
    }

    function saveRecentSearch(entry) {
        const list = getRecentSearches();
        list.unshift(entry);
        const trimmed = list.slice(0, 5);
        try {
            localStorage.setItem(RECENT_KEY, JSON.stringify(trimmed));
        } catch (err) {
            /* storage unavailable — fail silently */
        }
        renderRecentSearches();
    }

    function renderRecentSearches() {
        const list = getRecentSearches();
        if (!list.length) {
            recentWrapper.classList.add("hidden");
            return;
        }
        recentWrapper.classList.remove("hidden");
        recentList.innerHTML = list
            .map(
                (item) => `
        <button type="button" class="tsw-chip" data-recent="${item.label}">
            <i class="fa-solid fa-clock-rotate-left" aria-hidden="true"></i> ${item.label}
        </button>
    `,
            )
            .join("");
    }

    document.getElementById("tsw-clear-recent")?.addEventListener("click", () => {
        try {
            localStorage.removeItem(RECENT_KEY);
        } catch (err) {
            /* noop */
        }
        renderRecentSearches();
    });

    renderRecentSearches();

    /* =========================================================
    POPULAR SEARCHES -> APPLY TO FIELDS
    ========================================================= */
    function applyRouteToFields(label) {
        if (label.includes("→")) {
            const [from, to] = label.split("→").map((s) => s.trim());
            if (fromInput && toInput) {
                fromInput.value = from;
                toInput.value = to;
            }
        }
    }

    widget.querySelectorAll("[data-popular]").forEach((chip) => {
        chip.addEventListener("click", () => applyRouteToFields(chip.getAttribute("data-popular")));
    });

    widget.addEventListener("click", (e) => {
        const recentChip = e.target.closest("[data-recent]");
        if (recentChip) applyRouteToFields(recentChip.getAttribute("data-recent"));
    });

    /* =========================================================
    SEARCH BUTTON
    ========================================================= */
    document.getElementById("tsw-search-btn")?.addEventListener("click", () => {
        if (!validateActivePanel()) return;

        const activeTab = widget.querySelector(".tsw-tab.is-active");
        const label =
            fromInput && toInput && fromInput.value && toInput.value
                ? `${fromInput.value} → ${toInput.value}`
                : `${activeTab ? activeTab.textContent.trim() : "Search"}`;

        saveRecentSearch({ label, tab: activeTab?.getAttribute("data-tab") });

        // Integration point: submit search payload to backend / redirect to results page.
        // e.g. window.location.href = `/search-results?tab=${activeTab.dataset.tab}`;
    });
})();


// footer
(() => {
    'use strict';
    const yearEl = document.getElementById('footer-year');
    if (yearEl) yearEl.textContent = new Date().getFullYear();

    const newsletterForm = document.querySelector('#footer [aria-label="Newsletter signup"]');
    newsletterForm?.addEventListener('submit', (e) => {
        e.preventDefault();
        // Integration point: submit email to backend newsletter endpoint.
        if (window.App?.Toast) {
            window.App.Toast.success('Thanks for subscribing! Check your inbox to confirm.');
        }
        newsletterForm.reset();
    });
})();

