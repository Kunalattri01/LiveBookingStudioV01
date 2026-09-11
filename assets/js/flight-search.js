/* ================================================================
   SEA OF SEATS - FLIGHT SEARCH
   ================================================================
   Handles:

   - From airport popup
   - To airport popup
   - Swap airports
   - One Way / Round Trip / Multi City
   - Departure date
   - Return date
   - Travellers
   - Cabin class
   - Special fare
   - Price drop protection
   - Search validation
   - Responsive popup positioning
   - Popup positioning on scroll / resize
   - Escape / outside click
   - Works with both:
       data-flight-popover="..."
       and
       data-field="..."
   ================================================================ */

(function () {

    "use strict";


    /* ================================================================
       PREVENT DOUBLE INITIALIZATION
       ================================================================ */

    if (window.__SEA_OF_SEATS_FLIGHT_SEARCH_INITIALIZED__) {
        return;
    }

    window.__SEA_OF_SEATS_FLIGHT_SEARCH_INITIALIZED__ = true;


    /* ================================================================
       STATE
       ================================================================ */

    const state = {

        tripType: "oneway",

        origin: null,

        destination: null,

        departureDate: null,

        returnDate: null,

        adults: 1,

        children: 0,

        infants: 0,

        cabinClass: "economy",

        specialFare: "regular",

        priceDropProtection: false,

        activeButton: null,

        activeType: null,

        activeLocationType: null,

        calendarMonth: null

    };


    /* ================================================================
       AIRPORT DATA

       Backed by our own local airport/city master data (see the
       `flight` Django app), rendered into the page by the homepage
       view as window.__FLIGHT_AIRPORTS_SEED__. This is NOT TripJack
       data — it is our application's own master data and is used only
       for the From/To autocomplete UI.

       This array is also refreshed live from /flight/airports/?q=...
       as the user types (see fetchAirportsFromServer below), so it
       doubles as a client-side cache.
       ================================================================ */

    const airports = Array.isArray(window.__FLIGHT_AIRPORTS_SEED__)
        ? window.__FLIGHT_AIRPORTS_SEED__.slice()
        : [];


    let airportSearchDebounceTimer = null;


    function fetchAirportsFromServer(query) {

        return fetch(
            "/flight/airports/?q=" + encodeURIComponent(query || "")
        )
            .then(function (response) {

                if (!response.ok) {
                    throw new Error("Airport search request failed");
                }

                return response.json();

            })
            .then(function (data) {

                return (data && data.results) || [];

            })
            .catch(function () {

                // Network/server issue: signal failure so the caller
                // can keep showing whatever is already cached instead
                // of clearing the list.
                return null;

            });

    }


    function mergeAirportsIntoCache(items) {

        items.forEach(
            function (item) {

                const existingIndex =
                    airports.findIndex(
                        function (airport) {

                            return airport.code === item.code;

                        }
                    );


                if (existingIndex >= 0) {

                    airports[existingIndex] = item;

                }

                else {

                    airports.push(item);

                }

            }
        );

    }


    function filterLocalAirports(query) {

        const normalized =
            String(query || "")
                .trim()
                .toLowerCase();

        return airports.filter(
            function (airport) {

                return (

                    airport.code
                        .toLowerCase()
                        .includes(normalized)

                    ||

                    airport.city
                        .toLowerCase()
                        .includes(normalized)

                    ||

                    airport.airport
                        .toLowerCase()
                        .includes(normalized)

                );

            }
        );

    }


    /* ================================================================
       CABIN OPTIONS
       ================================================================ */

    const cabinOptions = [

        {
            value: "economy",
            title: "Economy / Premium Economy",
            shortTitle: "Economy",
            description: "Comfortable travel at an affordable fare",
            icon: "fa-chair"
        },

        {
            value: "premium_economy",
            title: "Premium Economy",
            shortTitle: "Premium Economy",
            description: "Extra legroom and additional comfort",
            icon: "fa-couch"
        },

        {
            value: "business",
            title: "Business Class",
            shortTitle: "Business Class",
            description: "Premium seating and enhanced services",
            icon: "fa-couch"
        },

        {
            value: "first",
            title: "First Class",
            shortTitle: "First Class",
            description: "Luxury seating and premium service",
            icon: "fa-couch"
        }

    ];


    /* ================================================================
       DOM HELPERS
       ================================================================ */

    function $(selector) {

        return document.querySelector(selector);

    }


    function $$(selector) {

        return Array.from(
            document.querySelectorAll(selector)
        );

    }


    /* ================================================================
       SAFE HTML ESCAPE
       ================================================================ */

    function escapeHTML(value) {

        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");

    }


    /* ================================================================
       DATE HELPERS
       ================================================================ */

    function startOfDay(date) {

        const result = new Date(date);

        result.setHours(
            0,
            0,
            0,
            0
        );

        return result;

    }


    function cloneDate(date) {

        if (!date) {
            return null;
        }

        return new Date(
            date.getFullYear(),
            date.getMonth(),
            date.getDate()
        );

    }


    function sameDate(first, second) {

        if (!first || !second) {
            return false;
        }

        return (
            first.getFullYear() === second.getFullYear() &&
            first.getMonth() === second.getMonth() &&
            first.getDate() === second.getDate()
        );

    }


    function formatDate(date) {

        if (!date) {
            return "--";
        }

        return new Intl.DateTimeFormat(
            "en-IN",
            {
                day: "numeric",
                month: "short",
                year: "2-digit"
            }
        ).format(date);

    }


    function formatWeekday(date) {

        if (!date) {
            return "";
        }

        return new Intl.DateTimeFormat(
            "en-IN",
            {
                weekday: "long"
            }
        ).format(date);

    }


    function formatMonth(date) {

        return new Intl.DateTimeFormat(
            "en-IN",
            {
                month: "long",
                year: "numeric"
            }
        ).format(date);

    }


    function formatAPIDate(date) {

        if (!date) {
            return "";
        }

        const year =
            date.getFullYear();

        const month =
            String(
                date.getMonth() + 1
            ).padStart(2, "0");

        const day =
            String(
                date.getDate()
            ).padStart(2, "0");

        return `${year}-${month}-${day}`;

    }


    function parseAPIDate(value) {

        if (!value) {
            return null;
        }

        const parts =
            String(value).split("-");

        if (parts.length !== 3) {
            return null;
        }

        const year =
            Number(parts[0]);

        const month =
            Number(parts[1]) - 1;

        const day =
            Number(parts[2]);

        if (
            !Number.isFinite(year) ||
            !Number.isFinite(month) ||
            !Number.isFinite(day)
        ) {
            return null;
        }

        return new Date(
            year,
            month,
            day
        );

    }


    /* ================================================================
       POPOVER ROOT
       ================================================================ */

    function getPopover() {

        return $("#flight-popover");

    }


    function ensurePopoverRoot() {

        let popover =
            getPopover();

        /*
         * If HTML already has #flight-popover,
         * move it outside hero/search containers.
         */

        if (popover) {

            if (
                popover.parentElement !==
                document.body
            ) {

                document.body.appendChild(
                    popover
                );

            }

        } else {

            /*
             * Fallback:
             * create popup automatically.
             */

            popover =
                document.createElement("div");

            popover.id =
                "flight-popover";

            popover.className =
                "flight-popover hidden";

            popover.setAttribute(
                "role",
                "dialog"
            );

            popover.setAttribute(
                "aria-modal",
                "false"
            );

            document.body.appendChild(
                popover
            );

        }


        /*
         * These styles are intentionally applied
         * by JS so positioning does not depend on
         * parent containers.
         */

        popover.style.position =
            "fixed";

        popover.style.zIndex =
            "100000";

        popover.style.boxSizing =
            "border-box";

        return popover;

    }


    /* ================================================================
       NORMALIZE FIELD TYPE

       Supports both versions of your HTML.

       Version 1:
       data-flight-popover="location"

       Version 2:
       data-field="travellers"
       ================================================================ */

    function getFieldInfo(button) {

        if (!button) {
            return null;
        }


        const popoverType =
            button.dataset.flightPopover;


        if (popoverType) {

            return {

                type: popoverType,

                locationType:
                    button.dataset.locationType ||
                    null,

                dateType:
                    button.dataset.dateType ||
                    null

            };

        }


        const field =
            button.dataset.field;


        if (!field) {
            return null;
        }


        if (
            field === "from" ||
            field === "to"
        ) {

            return {

                type: "location",

                locationType: field,

                dateType: null

            };

        }


        if (
            field === "departure" ||
            field === "return"
        ) {

            return {

                type: "date",

                locationType: null,

                dateType: field

            };

        }


        if (field === "travellers") {

            return {

                type: "travellers",

                locationType: null,

                dateType: null

            };

        }


        if (field === "cabin") {

            return {

                type: "cabin",

                locationType: null,

                dateType: null

            };

        }


        return null;

    }


    /* ================================================================
       FIND FLIGHT FIELD
       ================================================================ */

    function findField(type, value) {

        if (type === "location") {

            if (value === "from") {

                return $(
                    '[data-flight-popover="location"][data-location-type="from"]'
                ) || $(
                    '[data-field="from"]'
                );

            }

            if (value === "to") {

                return $(
                    '[data-flight-popover="location"][data-location-type="to"]'
                ) || $(
                    '[data-field="to"]'
                );

            }

        }


        if (type === "date") {

            if (value === "departure") {

                return $(
                    '[data-flight-popover="date"][data-date-type="departure"]'
                ) || $(
                    '#flight-departure-field'
                ) || $(
                    '[data-field="departure"]'
                );

            }

            if (value === "return") {

                return $(
                    '[data-flight-popover="date"][data-date-type="return"]'
                ) || $(
                    '#flight-return-field'
                ) || $(
                    '[data-field="return"]'
                );

            }

        }


        if (type === "travellers") {

            return $(
                '[data-flight-popover="travellers"]'
            ) || $(
                '#flight-traveller-field'
            ) || $(
                '[data-field="travellers"]'
            );

        }


        if (type === "cabin") {

            return $(
                '[data-flight-popover="cabin"]'
            ) || $(
                '#flight-cabin-field'
            ) || $(
                '[data-field="cabin"]'
            );

        }


        return null;

    }


    /* ================================================================
       CLOSE POPOVER
       ================================================================ */

    function closePopover() {

        const popover =
            getPopover();

        if (!popover) {
            return;
        }


        popover.classList.add(
            "hidden"
        );

        popover.innerHTML =
            "";

        popover.removeAttribute(
            "data-popover-type"
        );

        popover.style.left =
            "";

        popover.style.top =
            "";

        popover.style.width =
            "";

        popover.style.maxWidth =
            "";

        popover.style.maxHeight =
            "";

        popover.style.bottom =
            "auto";


        if (state.activeButton) {

            state.activeButton.setAttribute(
                "aria-expanded",
                "false"
            );

        }


        state.activeButton =
            null;

        state.activeType =
            null;

        state.activeLocationType =
            null;

    }


    /* ================================================================
       POPOVER WIDTH
       ================================================================ */

    function getPopoverWidth(type) {

        const viewport =
            window.innerWidth;


        if (viewport <= 640) {

            return Math.max(
                280,
                viewport - 24
            );

        }


        if (type === "location") {

            return Math.min(
                440,
                viewport - 24
            );

        }


        if (type === "date") {

            return Math.min(
                640,
                viewport - 24
            );

        }


        if (type === "travellers") {

            return Math.min(
                390,
                viewport - 24
            );

        }


        if (type === "cabin") {

            return Math.min(
                390,
                viewport - 24
            );

        }


        return Math.min(
            420,
            viewport - 24
        );

    }


    /* ================================================================
       POSITION POPOVER

       IMPORTANT:

       Uses viewport coordinates because popup is
       position: fixed and attached to body.
       ================================================================ */

    function positionPopover() {

        const popover =
            getPopover();

        const button =
            state.activeButton;


        if (
            !popover ||
            !button ||
            popover.classList.contains("hidden")
        ) {
            return;
        }


        const rect =
            button.getBoundingClientRect();


        const viewportWidth =
            window.innerWidth;

        const viewportHeight =
            window.innerHeight;


        const margin =
            12;

        const gap =
            8;


        /*
         * MOBILE
         *
         * Use centered popup.
         */

        if (
            viewportWidth <= 640
        ) {

            const mobileWidth =
                Math.min(
                    viewportWidth - 24,
                    520
                );


            popover.style.width =
                `${mobileWidth}px`;


            popover.style.maxWidth =
                `${mobileWidth}px`;


            popover.style.left =
                `${Math.max(
                    12,
                    (viewportWidth - mobileWidth) / 2
                )}px`;


            popover.style.top =
                `${12}px`;


            popover.style.maxHeight =
                `${viewportHeight - 24}px`;


            popover.style.overflowY =
                "auto";


            return;

        }


        /*
         * DESKTOP
         */

        const width =
            getPopoverWidth(
                state.activeType
            );


        popover.style.width =
            `${width}px`;


        popover.style.maxWidth =
            `calc(100vw - 24px)`;


        popover.style.maxHeight =
            `calc(100vh - 24px)`;


        popover.style.overflow =
            "hidden";


        /*
         * Start aligned with field.
         */

        let left =
            rect.left;


        /*
         * Prevent right overflow.
         */

        if (
            left + width >
            viewportWidth - margin
        ) {

            left =
                viewportWidth -
                width -
                margin;

        }


        /*
         * Prevent left overflow.
         */

        if (
            left < margin
        ) {

            left =
                margin;

        }


        /*
         * Popup height is now available
         * because popup has already been rendered.
         */

        const popupHeight =
            popover.offsetHeight;


        const spaceBelow =
            viewportHeight -
            rect.bottom -
            gap -
            margin;


        const spaceAbove =
            rect.top -
            gap -
            margin;


        let top;


        /*
         * Prefer below.
         */

        if (
            popupHeight <=
            spaceBelow
        ) {

            top =
                rect.bottom + gap;

        }

        /*
         * If it doesn't fit below,
         * use above when possible.
         */

        else if (
            popupHeight <=
            spaceAbove
        ) {

            top =
                rect.top -
                popupHeight -
                gap;

        }

        /*
         * Otherwise use the side
         * with more available room.
         */

        else if (
            spaceBelow >=
            spaceAbove
        ) {

            top =
                rect.bottom + gap;

        }

        else {

            top =
                rect.top -
                popupHeight -
                gap;

        }


        /*
         * Final viewport safety.
         */

        if (
            top < margin
        ) {

            top =
                margin;

        }


        if (
            top + popupHeight >
            viewportHeight - margin
        ) {

            top =
                Math.max(
                    margin,
                    viewportHeight -
                    popupHeight -
                    margin
                );

        }


        popover.style.left =
            `${Math.round(left)}px`;


        popover.style.top =
            `${Math.round(top)}px`;

    }


    /* ================================================================
       OPEN POPOVER
       ================================================================ */

    function openPopover(button) {

        const info =
            getFieldInfo(button);


        if (!info) {
            return;
        }


        const popover =
            ensurePopoverRoot();


        if (!popover) {
            return;
        }


        /*
         * Clicking same field closes it.
         */

        if (
            state.activeButton === button &&
            !popover.classList.contains("hidden")
        ) {

            closePopover();

            return;

        }


        closePopover();


        state.activeButton =
            button;

        state.activeType =
            info.type;

        state.activeLocationType =
            info.locationType;


        button.setAttribute(
            "aria-expanded",
            "true"
        );


        popover.dataset.popoverType =
            info.type;


        /*
         * Render popup.
         */

        if (
            info.type === "location"
        ) {

            renderLocationPopover(
                info.locationType
            );

        }

        else if (
            info.type === "date"
        ) {

            renderDatePopover(
                info.dateType
            );

        }

        else if (
            info.type === "travellers"
        ) {

            renderTravellerPopover();

        }

        else if (
            info.type === "cabin"
        ) {

            renderCabinPopover();

        }

        else {

            return;

        }


        popover.classList.remove(
            "hidden"
        );


        /*
         * Position after browser paints.
         */

        requestAnimationFrame(
            function () {

                positionPopover();

            }
        );

    }


    /* ================================================================
       LOCATION POPUP
       ================================================================ */

    function renderLocationPopover(type) {

        const popover =
            ensurePopoverRoot();


        if (!popover) {
            return;
        }


        const title =
            type === "from"
                ? "Select departure city"
                : "Select destination city";


        popover.innerHTML = `

            <div class="flight-popover-header">

                <i
                    class="fa-solid fa-magnifying-glass"
                    aria-hidden="true">
                </i>

                <input
                    type="search"
                    id="flight-location-search"
                    autocomplete="off"
                    placeholder="${escapeHTML(title)}"
                    aria-label="${escapeHTML(title)}"
                >

                <button
                    type="button"
                    class="flight-popover-close"
                    id="flight-popover-close"
                    aria-label="Close"
                >
                    <i
                        class="fa-solid fa-xmark"
                        aria-hidden="true">
                    </i>
                </button>

            </div>

            <div class="flight-popover-section-title">
                Popular Airports
            </div>

            <div
                class="flight-location-list"
                id="flight-location-list">
            </div>

        `;


        renderAirportList("");


        const input =
            $("#flight-location-search");


        if (input) {

            input.addEventListener(
                "input",
                function () {

                    renderAirportList(
                        input.value
                    );

                }
            );


            setTimeout(
                function () {

                    input.focus();

                },
                20
            );

        }


        bindPopoverCloseButton();

    }


    /* ================================================================
       AIRPORT LIST
       ================================================================ */

    function renderAirportListItems(results) {

        const list =
            $("#flight-location-list");


        if (!list) {
            return;
        }


        if (!results.length) {

            list.innerHTML = `

                <div class="flight-empty-state">
                    No airport found.
                </div>

            `;

            return;

        }


        list.innerHTML =
            results.map(
                function (airport) {

                    return `

                        <button
                            type="button"
                            class="flight-location-option"
                            data-airport-code="${escapeHTML(airport.code)}"
                        >

                            <span class="flight-location-code">
                                ${escapeHTML(airport.code)}
                            </span>

                            <span class="flight-location-copy">

                                <strong>
                                    ${escapeHTML(airport.city)}
                                </strong>

                                <small>
                                    ${escapeHTML(airport.airport)}
                                </small>

                            </span>

                        </button>

                    `;

                }
            ).join("");


        $$("#flight-location-list [data-airport-code]")
            .forEach(
                function (button) {

                    button.addEventListener(
                        "click",
                        function () {

                            selectAirport(
                                button.dataset.airportCode,
                                state.activeLocationType
                            );

                        }
                    );

                }
            );

    }


    function renderAirportList(search) {

        const list =
            $("#flight-location-list");


        if (!list) {
            return;
        }


        /*
         * Render instantly from whatever we already have (seeded
         * master data / previous server responses) so the popover
         * never feels laggy, then refresh from the backend.
         */

        renderAirportListItems(
            filterLocalAirports(search)
        );


        clearTimeout(airportSearchDebounceTimer);

        airportSearchDebounceTimer = setTimeout(
            function () {

                fetchAirportsFromServer(search).then(
                    function (results) {

                        if (results === null) {

                            // Request failed - keep showing the
                            // local/cached results rendered above.
                            return;

                        }


                        mergeAirportsIntoCache(results);

                        renderAirportListItems(results);

                    }
                );

            },
            150
        );

    }


    /* ================================================================
       SELECT AIRPORT
       ================================================================ */

    function selectAirport(code, type) {

        const airport =
            airports.find(
                function (item) {

                    return item.code === code;

                }
            );


        if (!airport) {
            return;
        }


        if (type === "from") {

            state.origin =
                airport;


            updateSummary();


            closePopover();


            /*
             * Automatically open destination.
             */

            const destinationButton =
                findField(
                    "location",
                    "to"
                );


            if (destinationButton) {

                setTimeout(
                    function () {

                        openPopover(
                            destinationButton
                        );

                    },
                    120
                );

            }

        }

        else {

            state.destination =
                airport;


            updateSummary();

            closePopover();

        }

    }


    /* ================================================================
       SWAP LOCATIONS
       ================================================================ */

    function swapLocations() {

        const oldOrigin =
            state.origin;


        state.origin =
            state.destination;


        state.destination =
            oldOrigin;


        updateSummary();

    }


    /* ================================================================
       DATE POPUP
       ================================================================ */

    function renderDatePopover(type) {

        const popover =
            ensurePopoverRoot();


        if (!popover) {
            return;
        }


        /*
         * Return date requires departure.
         */

        if (
            type === "return" &&
            !state.departureDate
        ) {

            alert(
                "Please select your departure date first."
            );

            closePopover();

            return;

        }


        /*
         * Start calendar from selected
         * departure month or current month.
         */

        if (
            state.departureDate
        ) {

            state.calendarMonth =
                cloneDate(
                    state.departureDate
                );

        }

        else {

            state.calendarMonth =
                startOfDay(
                    new Date()
                );

        }


        state.calendarMonth.setDate(1);


        popover.innerHTML = `

            <div class="flight-popover-header flight-date-header">

                <strong>
                    ${
                        type === "departure"
                            ? "Select departure date"
                            : "Select return date"
                    }
                </strong>

                <span>
                    ${
                        type === "departure"
                            ? "Choose your travel date"
                            : "Choose your return date"
                    }
                </span>

                <button
                    type="button"
                    class="flight-popover-close"
                    id="flight-popover-close"
                    aria-label="Close"
                >
                    <i
                        class="fa-solid fa-xmark"
                        aria-hidden="true">
                    </i>
                </button>

            </div>

            <div
                class="flight-calendar"
                id="flight-calendar">
            </div>

        `;


        renderCalendar(type);


        bindPopoverCloseButton();

    }


    /* ================================================================
       CALENDAR
       ================================================================ */

    function renderCalendar(type) {

        const calendar =
            $("#flight-calendar");


        if (!calendar) {
            return;
        }


        const firstMonth =
            cloneDate(
                state.calendarMonth ||
                startOfDay(new Date())
            );


        firstMonth.setDate(1);


        const secondMonth =
            cloneDate(firstMonth);


        secondMonth.setMonth(
            secondMonth.getMonth() + 1
        );


        calendar.innerHTML = `

            <div class="flight-calendar-toolbar">

                <button
                    type="button"
                    class="flight-calendar-nav"
                    data-calendar-action="previous"
                    aria-label="Previous month"
                >
                    <i
                        class="fa-solid fa-chevron-left"
                        aria-hidden="true">
                    </i>
                </button>

                <div class="flight-calendar-month-label">
                    ${escapeHTML(formatMonth(firstMonth))}
                </div>

                <div class="flight-calendar-month-label">
                    ${escapeHTML(formatMonth(secondMonth))}
                </div>

                <button
                    type="button"
                    class="flight-calendar-nav"
                    data-calendar-action="next"
                    aria-label="Next month"
                >
                    <i
                        class="fa-solid fa-chevron-right"
                        aria-hidden="true">
                    </i>
                </button>

            </div>

            <div class="flight-calendar-months">

                ${renderCalendarMonth(
                    firstMonth,
                    type
                )}

                ${renderCalendarMonth(
                    secondMonth,
                    type
                )}

            </div>

        `;


        /*
         * Previous month.
         */

        const previous =
            calendar.querySelector(
                '[data-calendar-action="previous"]'
            );


        if (previous) {

            previous.addEventListener(
                "click",
                function (event) {

                    event.stopPropagation();


                    state.calendarMonth.setMonth(
                        state.calendarMonth.getMonth() - 1
                    );


                    renderCalendar(type);

                }
            );

        }


        /*
         * Next month.
         */

        const next =
            calendar.querySelector(
                '[data-calendar-action="next"]'
            );


        if (next) {

            next.addEventListener(
                "click",
                function (event) {

                    event.stopPropagation();


                    state.calendarMonth.setMonth(
                        state.calendarMonth.getMonth() + 1
                    );


                    renderCalendar(type);

                }
            );

        }


        /*
         * Dates.
         */

        $$("#flight-calendar [data-calendar-date]")
            .forEach(
                function (button) {

                    button.addEventListener(
                        "click",
                        function () {

                            if (
                                button.disabled
                            ) {
                                return;
                            }


                            const selectedDate =
                                parseAPIDate(
                                    button.dataset.calendarDate
                                );


                            if (!selectedDate) {
                                return;
                            }


                            selectDate(
                                selectedDate,
                                type
                            );

                        }
                    );

                }
            );


        /*
         * Recalculate popup position
         * because calendar height can change.
         */

        requestAnimationFrame(
            positionPopover
        );

    }


    /* ================================================================
       CALENDAR MONTH
       ================================================================ */

    function renderCalendarMonth(
        monthDate,
        type
    ) {

        const year =
            monthDate.getFullYear();


        const month =
            monthDate.getMonth();


        const firstDay =
            new Date(
                year,
                month,
                1
            );


        const lastDay =
            new Date(
                year,
                month + 1,
                0
            );


        const startDay =
            firstDay.getDay();


        const today =
            startOfDay(
                new Date()
            );


        let html = `

            <div class="flight-calendar-month">

                <div class="flight-calendar-month-title">
                    ${escapeHTML(formatMonth(monthDate))}
                </div>

                <div class="flight-calendar-weekdays">

                    <span>Su</span>
                    <span>Mo</span>
                    <span>Tu</span>
                    <span>We</span>
                    <span>Th</span>
                    <span>Fr</span>
                    <span>Sa</span>

                </div>

                <div class="flight-calendar-days">

        `;


        /*
         * Empty cells.
         */

        for (
            let i = 0;
            i < startDay;
            i++
        ) {

            html += `

                <span class="flight-calendar-empty"></span>

            `;

        }


        /*
         * Actual dates.
         */

        for (
            let day = 1;
            day <= lastDay.getDate();
            day++
        ) {

            const date =
                new Date(
                    year,
                    month,
                    day
                );


            let disabled =
                date < today;


            /*
             * Return cannot be before departure.
             */

            if (
                type === "return" &&
                state.departureDate &&
                date <
                startOfDay(
                    state.departureDate
                )
            ) {

                disabled = true;

            }


            const selected =
                type === "departure"
                    ? sameDate(
                        date,
                        state.departureDate
                    )
                    : sameDate(
                        date,
                        state.returnDate
                    );


            let classes =
                "flight-calendar-day";


            if (disabled) {

                classes +=
                    " is-disabled";

            }


            if (selected) {

                classes +=
                    " is-selected";

            }


            html += `

                <button
                    type="button"
                    class="${classes}"
                    data-calendar-date="${formatAPIDate(date)}"
                    ${disabled ? "disabled" : ""}
                >
                    ${day}
                </button>

            `;

        }


        html += `

                </div>

            </div>

        `;


        return html;

    }


    /* ================================================================
       SELECT DATE
       ================================================================ */

    function selectDate(
        date,
        type
    ) {

        const selected =
            startOfDay(date);


        if (
            type === "departure"
        ) {

            state.departureDate =
                selected;


            /*
             * Existing return date becomes
             * invalid if it is now before departure.
             */

            if (
                state.returnDate &&
                state.returnDate <
                state.departureDate
            ) {

                state.returnDate =
                    null;

            }


            updateSummary();

            closePopover();


            /*
             * Round trip:
             * automatically open return.
             */

            if (
                state.tripType ===
                "roundtrip"
            ) {

                const returnButton =
                    findField(
                        "date",
                        "return"
                    );


                if (returnButton) {

                    setTimeout(
                        function () {

                            openPopover(
                                returnButton
                            );

                        },
                        120
                    );

                }

            }


            return;

        }


        /*
         * RETURN DATE
         */

        if (
            type === "return"
        ) {

            if (
                state.departureDate &&
                selected <
                state.departureDate
            ) {

                alert(
                    "Return date cannot be before departure date."
                );

                return;

            }


            state.returnDate =
                selected;


            updateSummary();

            closePopover();

        }

    }


    /* ================================================================
       TRAVELLER POPUP
       ================================================================ */

    function renderTravellerPopover() {

        const popover =
            ensurePopoverRoot();


        if (!popover) {
            return;
        }


        popover.innerHTML = `

            <div class="flight-popover-header">

                <strong>
                    Travellers
                </strong>

                <button
                    type="button"
                    class="flight-popover-close"
                    id="flight-popover-close"
                    aria-label="Close"
                >
                    <i
                        class="fa-solid fa-xmark"
                        aria-hidden="true">
                    </i>
                </button>

            </div>

            <div class="flight-counter-list">

                ${travellerRow(
                    "adults",
                    "Adults",
                    "12+ years",
                    state.adults,
                    1,
                    9
                )}

                ${travellerRow(
                    "children",
                    "Children",
                    "2 - 11 years",
                    state.children,
                    0,
                    8
                )}

                ${travellerRow(
                    "infants",
                    "Infants",
                    "Below 2 years",
                    state.infants,
                    0,
                    8
                )}

            </div>

            <div class="flight-date-actions">

                <span class="flight-traveller-note">
                    Infants cannot exceed adults.
                </span>

                <button
                    type="button"
                    class="flight-primary-btn"
                    id="flight-traveller-done"
                >
                    Done
                </button>

            </div>

        `;


        bindPopoverCloseButton();


        /*
         * Plus/minus buttons.
         */

        $$(
            "#flight-popover [data-traveller-action]"
        ).forEach(
            function (button) {

                button.addEventListener(
                    "click",
                    function (event) {

                        event.stopPropagation();


                        const travellerType =
                            button.dataset.travellerType;


                        const action =
                            button.dataset.travellerAction;


                        changeTraveller(
                            travellerType,
                            action
                        );

                    }
                );

            }
        );


        const done =
            $("#flight-traveller-done");


        if (done) {

            done.addEventListener(
                "click",
                function () {

                    closePopover();

                }
            );

        }

    }


    /* ================================================================
       TRAVELLER ROW
       ================================================================ */

    function travellerRow(
        type,
        title,
        description,
        count,
        min,
        max
    ) {

        const minusDisabled =
            count <= min;


        const plusDisabled =
            count >= max;


        return `

            <div class="flight-counter-row">

                <div>

                    <strong>
                        ${escapeHTML(title)}
                    </strong>

                    <small>
                        ${escapeHTML(description)}
                    </small>

                </div>

                <div class="flight-counter">

                    <button
                        type="button"
                        aria-label="Decrease ${escapeHTML(title)}"
                        data-traveller-type="${escapeHTML(type)}"
                        data-traveller-action="minus"
                        ${minusDisabled ? "disabled" : ""}
                    >
                        −
                    </button>

                    <span>
                        ${count}
                    </span>

                    <button
                        type="button"
                        aria-label="Increase ${escapeHTML(title)}"
                        data-traveller-type="${escapeHTML(type)}"
                        data-traveller-action="plus"
                        ${plusDisabled ? "disabled" : ""}
                    >
                        +
                    </button>

                </div>

            </div>

        `;

    }


    /* ================================================================
       CHANGE TRAVELLER
       ================================================================ */

    function changeTraveller(
        type,
        action
    ) {

        if (
            !Object.prototype.hasOwnProperty.call(
                state,
                type
            )
        ) {
            return;
        }


        let value =
            Number(state[type]);


        if (action === "plus") {

            value += 1;

        }

        else if (action === "minus") {

            value -= 1;

        }


        /*
         * Adults minimum 1.
         */

        if (
            type === "adults"
        ) {

            value =
                Math.max(
                    1,
                    Math.min(
                        9,
                        value
                    )
                );

        }

        else {

            value =
                Math.max(
                    0,
                    Math.min(
                        8,
                        value
                    )
                );

        }


        /*
         * Infants cannot exceed adults.
         */

        if (
            type === "infants"
        ) {

            value =
                Math.min(
                    value,
                    state.adults
                );

        }


        /*
         * If adults are reduced,
         * automatically reduce infants.
         */

        if (
            type === "adults" &&
            state.infants > value
        ) {

            state.infants =
                value;

        }


        state[type] =
            value;


        updateSummary();


        /*
         * Re-render popup.
         */

        renderTravellerPopover();


        requestAnimationFrame(
            positionPopover
        );

    }


    /* ================================================================
       CABIN POPUP
       ================================================================ */

    function renderCabinPopover() {

        const popover =
            ensurePopoverRoot();


        if (!popover) {
            return;
        }


        popover.innerHTML = `

            <div class="flight-popover-header">

                <strong>
                    Choose Cabin Class
                </strong>

                <button
                    type="button"
                    class="flight-popover-close"
                    id="flight-popover-close"
                    aria-label="Close"
                >
                    <i
                        class="fa-solid fa-xmark"
                        aria-hidden="true">
                    </i>
                </button>

            </div>

            <div class="flight-cabin-list">

                ${cabinOptions.map(
                    function (cabin) {

                        const selected =
                            cabin.value ===
                            state.cabinClass;


                        return `

                            <label
                                class="flight-cabin-option ${
                                    selected
                                        ? "is-selected"
                                        : ""
                                }"
                                data-cabin="${escapeHTML(cabin.value)}"
                            >

                                <input
                                    type="radio"
                                    name="flight-cabin-popup"
                                    value="${escapeHTML(cabin.value)}"
                                    ${
                                        selected
                                            ? "checked"
                                            : ""
                                    }
                                >

                                <span class="flight-cabin-radio"></span>

                                <span class="flight-cabin-copy">

                                    <strong>
                                        ${escapeHTML(cabin.title)}
                                    </strong>

                                    <small>
                                        ${escapeHTML(cabin.description)}
                                    </small>

                                </span>

                                <i
                                    class="fa-solid ${escapeHTML(cabin.icon)}"
                                    aria-hidden="true">
                                </i>

                            </label>

                        `;

                    }
                ).join("")}

            </div>

        `;


        bindPopoverCloseButton();


        $$("#flight-popover .flight-cabin-option")
            .forEach(
                function (option) {

                    option.addEventListener(
                        "click",
                        function () {

                            state.cabinClass =
                                option.dataset.cabin;


                            updateSummary();


                            /*
                             * Update selected state.
                             */

                            $$("#flight-popover .flight-cabin-option")
                                .forEach(
                                    function (item) {

                                        item.classList.toggle(
                                            "is-selected",
                                            item === option
                                        );

                                    }
                                );


                            const radio =
                                option.querySelector(
                                    "input"
                                );


                            if (radio) {
                                radio.checked =
                                    true;
                            }


                            /*
                             * Close after selection.
                             */

                            setTimeout(
                                closePopover,
                                100
                            );

                        }
                    );

                }
            );

    }


    /* ================================================================
       CLOSE BUTTON
       ================================================================ */

    function bindPopoverCloseButton() {

        const closeButton =
            $("#flight-popover-close");


        if (!closeButton) {
            return;
        }


        closeButton.addEventListener(
            "click",
            function (event) {

                event.preventDefault();

                event.stopPropagation();

                closePopover();

            }
        );

    }


    /* ================================================================
       UPDATE SUMMARY
       ================================================================ */

    function updateSummary() {

        /*
         * ------------------------------------------------------------
         * FROM
         * ------------------------------------------------------------
         */

        const fromValue =
            $("#flight-from-value");


        const fromSub =
            $("#flight-from-sub");


        if (fromValue) {

            fromValue.textContent =
                state.origin
                    ? state.origin.city
                    : "Select city";

        }


        if (fromSub) {

            fromSub.textContent =
                state.origin
                    ? `${state.origin.code}, ${state.origin.airport}`
                    : "Choose departure airport";

        }


        /*
         * ------------------------------------------------------------
         * TO
         * ------------------------------------------------------------
         */

        const toValue =
            $("#flight-to-value");


        const toSub =
            $("#flight-to-sub");


        if (toValue) {

            toValue.textContent =
                state.destination
                    ? state.destination.city
                    : "Select city";

        }


        if (toSub) {

            toSub.textContent =
                state.destination
                    ? `${state.destination.code}, ${state.destination.airport}`
                    : "Choose arrival airport";

        }


        /*
         * ------------------------------------------------------------
         * DEPARTURE
         * ------------------------------------------------------------
         */

        const departureValue =
            $("#flight-departure-value");


        const departureSub =
            $("#flight-departure-sub");


        if (departureValue) {

            departureValue.textContent =
                state.departureDate
                    ? formatDate(
                        state.departureDate
                    )
                    : "--";

        }


        if (departureSub) {

            departureSub.textContent =
                state.departureDate
                    ? formatWeekday(
                        state.departureDate
                    )
                    : "Select departure date";

        }


        /*
         * ------------------------------------------------------------
         * RETURN
         * ------------------------------------------------------------
         */

        const returnValue =
            $("#flight-return-value");


        const returnSub =
            $("#flight-return-sub");


        if (returnValue) {

            returnValue.textContent =
                state.returnDate
                    ? formatDate(
                        state.returnDate
                    )
                    : "Add return date";

        }


        if (returnSub) {

            returnSub.textContent =
                state.returnDate
                    ? formatWeekday(
                        state.returnDate
                    )
                    : "For bigger discounts";

        }


        /*
         * ------------------------------------------------------------
         * TRAVELLERS
         * ------------------------------------------------------------
         */

        const travellerSummary =
            $("#flight-traveller-summary");


        if (travellerSummary) {

            const adult =
                travellerSummary.querySelector(
                    '[data-count="adults"]'
                );


            const child =
                travellerSummary.querySelector(
                    '[data-count="children"]'
                );


            const infant =
                travellerSummary.querySelector(
                    '[data-count="infants"]'
                );


            if (adult) {
                adult.textContent =
                    state.adults;
            }


            if (child) {
                child.textContent =
                    state.children;
            }


            if (infant) {
                infant.textContent =
                    state.infants;
            }

        }


        /*
         * ------------------------------------------------------------
         * CABIN
         * ------------------------------------------------------------
         */

        const cabin =
            cabinOptions.find(
                function (item) {

                    return (
                        item.value ===
                        state.cabinClass
                    );

                }
            );


        const cabinValue =
            $("#flight-cabin-value");


        if (cabinValue) {

            cabinValue.textContent =
                cabin
                    ? cabin.shortTitle
                    : "Economy";

        }


        /*
         * Your other HTML version uses:
         * #cabin-class-summary
         */

        const cabinSummary =
            $("#cabin-class-summary");


        if (cabinSummary) {

            cabinSummary.textContent =
                cabin
                    ? cabin.shortTitle
                    : "Economy";

        }


        /*
         * ------------------------------------------------------------
         * HIDDEN INPUTS
         * ------------------------------------------------------------
         */

        setHidden(
            "#flight-origin-code",
            state.origin
                ? state.origin.code
                : ""
        );


        setHidden(
            "#flight-destination-code",
            state.destination
                ? state.destination.code
                : ""
        );


        setHidden(
            "#flight-departure-date",
            formatAPIDate(
                state.departureDate
            )
        );


        setHidden(
            "#flight-return-date",
            formatAPIDate(
                state.returnDate
            )
        );


        setHidden(
            "#flight-trip-type",
            state.tripType
        );


        setHidden(
            "#flight-adults",
            state.adults
        );


        setHidden(
            "#flight-children",
            state.children
        );


        setHidden(
            "#flight-infants",
            state.infants
        );


        setHidden(
            "#flight-cabin",
            state.cabinClass
        );

    }


    /* ================================================================
       SET HIDDEN INPUT
       ================================================================ */

    function setHidden(
        selector,
        value
    ) {

        const element =
            $(selector);


        if (element) {

            element.value =
                String(value ?? "");

        }

    }


    /* ================================================================
       DEFAULT STATE
       ================================================================ */

    function initializeDefaults() {

        /*
         * Default origin.
         */

        const originCode =
            $("#flight-origin-code")?.value ||
            "DEL";


        const destinationCode =
            $("#flight-destination-code")?.value ||
            "BOM";


        state.origin =
            airports.find(
                function (airport) {

                    return (
                        airport.code ===
                        originCode
                    );

                }
            ) ||
            airports[0];


        state.destination =
            airports.find(
                function (airport) {

                    return (
                        airport.code ===
                        destinationCode
                    );

                }
            ) ||
            airports[1];


        /*
         * Existing departure date.
         */

        const departureValue =
            $("#flight-departure-date")?.value;


        if (departureValue) {

            state.departureDate =
                parseAPIDate(
                    departureValue
                );

        }


        /*
         * If no date exists,
         * default to tomorrow.
         */

        if (!state.departureDate) {

            const tomorrow =
                startOfDay(
                    new Date()
                );


            tomorrow.setDate(
                tomorrow.getDate() + 1
            );


            state.departureDate =
                tomorrow;

        }


        /*
         * Existing return date.
         */

        const returnValue =
            $("#flight-return-date")?.value;


        if (returnValue) {

            state.returnDate =
                parseAPIDate(
                    returnValue
                );

        }


        /*
         * Trip type.
         */

        const tripType =
            $("#flight-trip-type")?.value;


        if (
            tripType === "oneway" ||
            tripType === "roundtrip" ||
            tripType === "multicity"
        ) {

            state.tripType =
                tripType;

        }


        /*
         * Travellers.
         */

        const adults =
            parseInt(
                $("#flight-adults")?.value ||
                "1",
                10
            );


        const children =
            parseInt(
                $("#flight-children")?.value ||
                "0",
                10
            );


        const infants =
            parseInt(
                $("#flight-infants")?.value ||
                "0",
                10
            );


        state.adults =
            Math.max(
                1,
                Math.min(
                    9,
                    Number.isFinite(adults)
                        ? adults
                        : 1
                )
            );


        state.children =
            Math.max(
                0,
                Math.min(
                    8,
                    Number.isFinite(children)
                        ? children
                        : 0
                )
            );


        state.infants =
            Math.max(
                0,
                Math.min(
                    state.adults,
                    Number.isFinite(infants)
                        ? infants
                        : 0
                )
            );


        /*
         * Cabin.
         */

        const cabin =
            $("#flight-cabin")?.value;


        if (
            cabinOptions.some(
                function (item) {

                    return item.value === cabin;

                }
            )
        ) {

            state.cabinClass =
                cabin;

        }


        /*
         * Special fare.
         */

        const selectedFare =
            $('input[name="special-fare"]:checked');


        if (selectedFare) {

            state.specialFare =
                selectedFare.value;

        }


        updateSummary();

    }


    /* ================================================================
       TRIP TYPE
       ================================================================ */

    function bindTripType() {

        $$(
            'input[name="trip-type"]'
        ).forEach(
            function (radio) {

                radio.addEventListener(
                    "change",
                    function () {

                        if (!radio.checked) {
                            return;
                        }


                        state.tripType =
                            radio.value;


                        if (
                            state.tripType ===
                            "oneway"
                        ) {

                            state.returnDate =
                                null;

                        }


                        updateSummary();

                    }
                );

            }
        );

    }


    /* ================================================================
       SPECIAL FARE
       ================================================================ */

    function bindSpecialFare() {

        $$(
            'input[name="special-fare"]'
        ).forEach(
            function (radio) {

                radio.addEventListener(
                    "change",
                    function () {

                        if (
                            radio.checked
                        ) {

                            state.specialFare =
                                radio.value;

                        }

                    }
                );

            }
        );

    }


    /* ================================================================
       PRICE DROP PROTECTION
       ================================================================ */

    function bindPriceDropProtection() {

        const checkbox =
            $("#price-drop-protection");


        if (!checkbox) {
            return;
        }


        checkbox.addEventListener(
            "change",
            function () {

                state.priceDropProtection =
                    checkbox.checked;

            }
        );

    }


    /* ================================================================
       POPUP FIELD EVENTS

       Uses event delegation so it works even
       if HTML is dynamically replaced.
       ================================================================ */

    function bindPopoverFields() {

        document.addEventListener(
            "click",
            function (event) {

                const button =
                    event.target.closest(
                        "[data-flight-popover], [data-field]"
                    );


                if (!button) {
                    return;
                }


                const info =
                    getFieldInfo(button);


                if (!info) {
                    return;
                }


                /*
                 * Don't hijack radio inputs,
                 * fare cards, etc.
                 */

                if (
                    button.tagName === "INPUT"
                ) {
                    return;
                }


                event.preventDefault();

                event.stopPropagation();


                openPopover(
                    button
                );

            },
            true
        );

    }


    /* ================================================================
       SWAP BUTTON
       ================================================================ */

    function bindSwapButton() {

        document.addEventListener(
            "click",
            function (event) {

                const button =
                    event.target.closest(
                        "#swap-locations"
                    );


                if (!button) {
                    return;
                }


                event.preventDefault();

                event.stopPropagation();


                swapLocations();

            },
            true
        );

    }


    /* ================================================================
       OUTSIDE CLICK
       ================================================================ */

    function bindOutsideClick() {

        document.addEventListener(
            "click",
            function (event) {

                const popover =
                    getPopover();


                if (
                    !popover ||
                    popover.classList.contains(
                        "hidden"
                    )
                ) {
                    return;
                }


                /*
                 * Click inside popup.
                 */

                if (
                    event.target.closest(
                        "#flight-popover"
                    )
                ) {
                    return;
                }


                /*
                 * Click on field.
                 */

                if (
                    event.target.closest(
                        "[data-flight-popover], [data-field]"
                    )
                ) {
                    return;
                }


                closePopover();

            }
        );

    }


    /* ================================================================
       ESCAPE KEY
       ================================================================ */

    function bindEscape() {

        document.addEventListener(
            "keydown",
            function (event) {

                if (
                    event.key === "Escape"
                ) {

                    closePopover();

                }

            }
        );

    }


    /* ================================================================
       SCROLL / RESIZE
       ================================================================ */

    function bindViewportEvents() {

        window.addEventListener(
            "resize",
            function () {

                if (
                    state.activeButton
                ) {

                    positionPopover();

                }

            }
        );


        /*
         * Capture scrolling from parent
         * containers as well.
         */

        window.addEventListener(
            "scroll",
            function () {

                if (
                    state.activeButton
                ) {

                    positionPopover();

                }

            },
            true
        );

    }


    /* ================================================================
       SEARCH URL
       ================================================================ */

    function buildSearchURL() {

        if (
            state.tripType ===
            "multicity" &&
            window.MultiCitySearch
        ) {

            const params =
                new URLSearchParams();


            params.set(
                "trip_type",
                "multicity"
            );


            params.set(
                "segments",
                JSON.stringify(
                    window.MultiCitySearch.getSegments()
                )
            );


            params.set(
                "adults",
                String(state.adults)
            );


            params.set(
                "children",
                String(state.children)
            );


            params.set(
                "infants",
                String(state.infants)
            );


            params.set(
                "cabin_class",
                state.cabinClass
            );


            params.set(
                "special_fare",
                state.specialFare
            );


            return (
                `/flight/results/?${params.toString()}`
            );

        }


        const params =
            new URLSearchParams();


        params.set(
            "trip_type",
            state.tripType
        );


        params.set(
            "origin",
            state.origin
                ? state.origin.code
                : ""
        );


        params.set(
            "destination",
            state.destination
                ? state.destination.code
                : ""
        );


        params.set(
            "departure_date",
            formatAPIDate(
                state.departureDate
            )
        );


        if (
            state.returnDate
        ) {

            params.set(
                "return_date",
                formatAPIDate(
                    state.returnDate
                )
            );

        }


        params.set(
            "adults",
            String(
                state.adults
            )
        );


        params.set(
            "children",
            String(
                state.children
            )
        );


        params.set(
            "infants",
            String(
                state.infants
            )
        );


        params.set(
            "cabin_class",
            state.cabinClass
        );


        params.set(
            "special_fare",
            state.specialFare
        );


        params.set(
            "price_drop_protection",
            state.priceDropProtection
                ? "1"
                : "0"
        );


        return (
            `/flight/results/?${params.toString()}`
        );

    }


    /* ================================================================
       SEARCH VALIDATION
       ================================================================ */

    function validateSearch() {

        if (
            state.tripType ===
            "multicity"
        ) {

            if (
                window.MultiCitySearch &&
                typeof window.MultiCitySearch.validate ===
                "function"
            ) {

                return window.MultiCitySearch.validate();

            }


            return (
                "Multi City search is not available right now."
            );

        }


        if (!state.origin) {

            return (
                "Please select your departure city."
            );

        }


        if (!state.destination) {

            return (
                "Please select your destination."
            );

        }


        if (
            state.origin.code ===
            state.destination.code
        ) {

            return (
                "Departure and destination cannot be the same."
            );

        }


        if (
            !state.departureDate
        ) {

            return (
                "Please select a departure date."
            );

        }


        if (
            state.tripType ===
            "roundtrip" &&
            !state.returnDate
        ) {

            return (
                "Please select a return date."
            );

        }


        if (
            state.returnDate &&
            state.departureDate &&
            state.returnDate <
            state.departureDate
        ) {

            return (
                "Return date cannot be before departure date."
            );

        }


        if (
            state.infants >
            state.adults
        ) {

            return (
                "Number of infants cannot exceed number of adults."
            );

        }


        return "";

    }


    /* ================================================================
       SEARCH BUTTON

       Supports:
       #flight-search-submit
       and button/input with data-flight-search
       ================================================================ */

    function bindSearchButton() {

        document.addEventListener(
            "click",
            function (event) {

                const button =
                    event.target.closest(
                        "#flight-search-submit, [data-flight-search]"
                    );


                if (!button) {
                    return;
                }


                event.preventDefault();

                event.stopPropagation();


                closePopover();


                /*
                 * Make sure state is synced.
                 */

                updateSummary();


                const error =
                    validateSearch();


                if (error) {

                    alert(error);

                    return;

                }


                /*
                 * Redirect to Django result page.
                 */

                window.location.href =
                    buildSearchURL();

            },
            true
        );

    }


    /* ================================================================
       FORM SUBMIT SUPPORT

       This is useful if the search button is
       inside a <form>.
       ================================================================ */

    function bindFormSubmit() {

        document.addEventListener(
            "submit",
            function (event) {

                const form =
                    event.target;


                if (
                    !form ||
                    !(
                        form.matches(
                            "#flight-search-form"
                        ) ||
                        form.querySelector(
                            "#flight-search-submit"
                        )
                    )
                ) {

                    return;

                }


                event.preventDefault();


                closePopover();


                updateSummary();


                const error =
                    validateSearch();


                if (error) {

                    alert(error);

                    return;

                }


                window.location.href =
                    buildSearchURL();

            },
            true
        );

    }


    /* ================================================================
       INITIALIZE
       ================================================================ */

    function initialize() {

        /*
         * Make popup body-level immediately.
         */

        ensurePopoverRoot();


        /*
         * Initialize state.
         */

        initializeDefaults();


        /*
         * Bind interactions.
         */

        bindPopoverFields();

        bindSwapButton();

        bindTripType();

        bindSpecialFare();

        bindPriceDropProtection();

        bindSearchButton();

        bindFormSubmit();

        bindOutsideClick();

        bindEscape();

        bindViewportEvents();


        /*
         * Make sure popup is closed initially.
         */

        closePopover();


        /*
         * Sync UI one final time.
         */

        updateSummary();

    }


    /* ================================================================
       START
       ================================================================ */

    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            initialize,
            {
                once: true
            }
        );

    }

    else {

        initialize();

    }


    /* ================================================================
       OPTIONAL GLOBAL ACCESS

       Useful if you need to debug from browser console.
       ================================================================ */

    window.SeaOfSeatsFlightSearch = {

        state: state,

        airports: airports,

        openPopover: openPopover,

        closePopover: closePopover,

        updateSummary: updateSummary,

        buildSearchURL: buildSearchURL

    };


})();