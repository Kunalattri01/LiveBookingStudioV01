/* ================================================================
   FLIGHT RESULTS / SHOPPING PAGE
   - Searches through our own API only.
   - Uses only provider-independent normalized flight data.
   - Supports filtering, sorting and selecting one flight per leg.
   ================================================================ */
(function () {
    "use strict";

    const searchRequest = window.__FLIGHT_SEARCH_REQUEST__;
    let allFlights = [];
    let activeStopsFilter = new Set();
    let activeAirlineFilter = new Set();
    let activeDepartureFilter = new Set();
    let activeArrivalFilter = new Set();
    let activeBaggageFilter = new Set();
    let refundableOnly = false;
    let maxPrice = null;
    let activeSort = "recommended";
    const selectedFlights = new Map();
    const selectedFares = new Map();
    let fareModalFlightKey = null;
    const RESULTS_PAGE_SIZE = Number(window.__FLIGHT_RESULTS_PAGE_SIZE__ || 20);
    let visibleFlightCount = RESULTS_PAGE_SIZE;

    function $(selector, root) { return (root || document).querySelector(selector); }
    function $$(selector, root) { return Array.from((root || document).querySelectorAll(selector)); }
    function show(el) { if (el) el.classList.remove("hidden"); }
    function hide(el) { if (el) el.classList.add("hidden"); }

    function formatDuration(minutes) {
        if (typeof minutes !== "number") return "—";
        return Math.floor(minutes / 60) + "h " + String(minutes % 60).padStart(2, "0") + "m";
    }

    function formatClock(value) {
        if (!value) return "--:--";
        const match = String(value).match(/T(\d{2}:\d{2})/);
        return match ? match[1] : String(value).slice(0, 5);
    }

    function hourOf(value) {
        if (!value) return null;
        const match = String(value).match(/T(\d{2}):/);
        if (!match) return null;
        return Number(match[1]);
    }

    function timeBucket(value) {
        const hour = hourOf(value);
        if (hour === null) return null;
        if (hour < 6) return "before6";
        if (hour < 12) return "morning";
        if (hour < 18) return "afternoon";
        return "evening";
    }

    function formatPrice(value, currency) {
        if (typeof value !== "number") return "Price on request";
        return (currency || "₹") + " " + value.toLocaleString("en-IN");
    }

    function cheapestFare(flight) {
        if (!flight.fares || !flight.fares.length) return null;
        return flight.fares.reduce(function (best, fare) {
            if (typeof fare.total_fare !== "number") return best;
            return !best || fare.total_fare < best.total_fare ? fare : best;
        }, null);
    }

    function flightKey(flight) {
        return [flight.leg_label || "RESULTS", flight.provider || "", flight.provider_reference || "", flight.segments?.map(function (s) { return s.segment_id || s.flight_number || ""; }).join(",")].join("|");
    }

    function legLabel(flight) { return flight.leg_label || "RESULTS"; }

    function runSearch() {
        if (!searchRequest) {
            showError("invalid_search_request", "Your search could not be read. Please search again from the homepage.");
            return;
        }

        fetch("/api/v1/flights/search/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(searchRequest)
        })
            .then(function (response) {
                return response.json().then(function (data) { return { status: response.status, data: data }; });
            })
            .then(function (result) {
                hide($("#flight-results-loading"));
                if (result.status !== 200 || !result.data.success) {
                    showError(result.data.error_code, result.data.error_message);
                    return;
                }
                allFlights = result.data.flights || [];
                selectedFlights.clear();
                if (!allFlights.length) {
                    show($("#flight-results-empty"));
                    return;
                }
                show($("#flight-results-header"));
                show($("#flight-quick-sort"));
                show($("#flight-filters-sidebar"));
                renderFilters(allFlights);
                updatePriceFilterBounds(allFlights);
                bindSelectionPanel();
                applyFiltersAndSort();
            })
            .catch(function () {
                hide($("#flight-results-loading"));
                showError("network_error", "We couldn't reach the search service. Please check your connection and try again.");
            });
    }

    function showError(errorCode, errorMessage) {
        const friendly = {
            flight_provider_not_configured: "Live flight search isn't configured yet on this environment.",
            provider_search_not_supported: "This search type isn't supported yet.",
            flight_provider_error: "The flight search provider didn't respond. Please try again in a moment.",
            invalid_search_request: errorMessage || "Please check your search and try again.",
            network_error: errorMessage
        };
        const message = $("#flight-results-error-message");
        if (message) message.textContent = friendly[errorCode] || errorMessage || "Something went wrong with your search.";
        show($("#flight-results-error"));
    }

    function uniqueAirlines(flights) {
        const map = {};
        flights.forEach(function (flight) {
            (flight.segments || []).forEach(function (segment) {
                if (segment.airline_code) map[segment.airline_code] = segment.airline_name || segment.airline_code;
            });
        });
        return map;
    }

    function renderFilters(flights) {
        const stopsCounts = { 0: 0, 1: 0, 2: 0 };
        flights.forEach(function (flight) { stopsCounts[Math.min(flight.stops || 0, 2)] += 1; });

        renderCheckboxGroup("#flight-filter-stops", "Stops", [
            { key: "0", label: "Non-stop" }, { key: "1", label: "1 Stop" }, { key: "2", label: "2+ Stops" }
        ].filter(function (x) { return stopsCounts[x.key]; }), stopsCounts, activeStopsFilter, applyFiltersAndSort);

        const airlines = uniqueAirlines(flights);
        const airlineContainer = $("#flight-filter-airlines");
        airlineContainer.innerHTML = '<h3 class="filter-title">Airlines</h3>';
        Object.keys(airlines).sort().forEach(function (code) {
            const label = document.createElement("label");
            label.className = "filter-option";
            const input = document.createElement("input");
            input.type = "checkbox";
            input.checked = activeAirlineFilter.has(code);
            input.addEventListener("change", function () {
                input.checked ? activeAirlineFilter.add(code) : activeAirlineFilter.delete(code);
                applyFiltersAndSort();
            });
            const name = document.createElement("span");
            name.className = "flex items-center gap-2";
            const logo = document.createElement("span");
            logo.className = "airline-mini-logo";
            logo.textContent = code;
            name.appendChild(logo);
            name.appendChild(document.createTextNode(airlines[code]));
            label.appendChild(input);
            label.appendChild(name);
            airlineContainer.appendChild(label);
        });

        renderSimpleTimeGroup("#flight-filter-departure", "Departure", activeDepartureFilter);
        renderSimpleTimeGroup("#flight-filter-arrival", "Arrival", activeArrivalFilter);

        const baggageContainer = $("#flight-filter-baggage");
        baggageContainer.innerHTML = '<h3 class="filter-title">Baggage</h3>';
        [
            { key: "checkin", label: "Check-in baggage" },
            { key: "cabin", label: "Cabin baggage" }
        ].forEach(function (entry) {
            const available = flights.some(function (flight) {
                const fare = cheapestFare(flight);
                return fare && fare.baggage && fare.baggage[entry.key];
            });
            if (!available) return;
            const label = document.createElement("label");
            label.className = "filter-option";
            const input = document.createElement("input");
            input.type = "checkbox";
            input.checked = activeBaggageFilter.has(entry.key);
            input.addEventListener("change", function () {
                input.checked ? activeBaggageFilter.add(entry.key) : activeBaggageFilter.delete(entry.key);
                applyFiltersAndSort();
            });
            label.appendChild(input);
            label.appendChild(document.createTextNode(entry.label));
            baggageContainer.appendChild(label);
        });

        const refundableAvailable = flights.some(function (flight) {
            const fare = cheapestFare(flight);
            return fare && typeof fare.refundable === "boolean";
        });
        const refundableContainer = $("#flight-filter-refundable");
        refundableContainer.innerHTML = '<h3 class="filter-title">Fare type</h3>';
        if (refundableAvailable) {
            const label = document.createElement("label");
            label.className = "filter-option";
            const input = document.createElement("input");
            input.type = "checkbox";
            input.checked = refundableOnly;
            input.addEventListener("change", function () { refundableOnly = input.checked; applyFiltersAndSort(); });
            label.appendChild(input);
            label.appendChild(document.createTextNode("Refundable only"));
            refundableContainer.appendChild(label);
        } else {
            const note = document.createElement("p");
            note.className = "text-[11px] text-text-secondary";
            note.textContent = "Refundability is not provided by this supplier response.";
            refundableContainer.appendChild(note);
        }
    }

    function renderCheckboxGroup(selector, title, entries, counts, state, callback) {
        const container = $(selector);
        container.innerHTML = '<h3 class="filter-title">' + title + '</h3>';
        entries.forEach(function (entry) {
            const label = document.createElement("label");
            label.className = "filter-option";
            const input = document.createElement("input");
            input.type = "checkbox";
            input.checked = state.has(entry.key);
            input.addEventListener("change", function () {
                input.checked ? state.add(entry.key) : state.delete(entry.key);
                callback();
            });
            label.appendChild(input);
            label.appendChild(document.createTextNode(entry.label));
            const count = document.createElement("span");
            count.className = "filter-price";
            count.textContent = counts[entry.key];
            label.appendChild(count);
            container.appendChild(label);
        });
    }

    function renderSimpleTimeGroup(selector, title, state) {
        const container = $(selector);
        container.innerHTML = '<h3 class="filter-title">' + title + '</h3>';
        [
            ["before6", "Before 6 AM"], ["morning", "6 AM – 12 PM"],
            ["afternoon", "12 PM – 6 PM"], ["evening", "6 PM – 12 AM"]
        ].forEach(function (entry) {
            const label = document.createElement("label");
            label.className = "filter-option";
            const input = document.createElement("input");
            input.type = "checkbox";
            input.checked = state.has(entry[0]);
            input.addEventListener("change", function () {
                input.checked ? state.add(entry[0]) : state.delete(entry[0]);
                applyFiltersAndSort();
            });
            label.appendChild(input);
            label.appendChild(document.createTextNode(entry[1]));
            container.appendChild(label);
        });
    }

    function updatePriceFilterBounds(flights) {
        const values = flights.map(cheapestFare).filter(Boolean).map(function (fare) { return fare.total_fare; }).filter(function (v) { return typeof v === "number"; });
        const container = $("#flight-filter-price");
        if (!container || !values.length) return;
        const min = Math.floor(Math.min.apply(null, values));
        const max = Math.ceil(Math.max.apply(null, values));
        maxPrice = max;
        container.innerHTML = '<h3 class="filter-title">Price</h3>' +
            '<div class="flex items-center justify-between text-xs text-text-secondary mb-2"><span>₹' + min.toLocaleString("en-IN") + '</span><span id="flight-price-max-label">₹' + max.toLocaleString("en-IN") + '</span></div>' +
            '<input id="flight-price-range" type="range" min="' + min + '" max="' + max + '" value="' + max + '" class="w-full accent-sky-500">' +
            '<p class="text-[11px] text-text-secondary mt-2">Up to <span id="flight-price-value">₹' + max.toLocaleString("en-IN") + '</span></p>';
        $("#flight-price-range").addEventListener("input", function () {
            maxPrice = Number(this.value);
            $("#flight-price-value").textContent = "₹" + maxPrice.toLocaleString("en-IN");
            applyFiltersAndSort();
        });
    }

    function airportOptionsHtml() {
        const airports = Array.isArray(window.__FLIGHT_AIRPORTS_SEED__) ? window.__FLIGHT_AIRPORTS_SEED__ : [];
        return airports.map(function (airport) {
            const option = document.createElement("option");
            option.value = airport.code;
            option.label = [airport.city, airport.airport].filter(Boolean).join(" · ");
            return option;
        });
    }

    function populateEditAirports() {
        const list = $("#flight-edit-airports");
        if (!list) return;
        list.innerHTML = "";
        airportOptionsHtml().forEach(function (option) { list.appendChild(option); });
    }

    function currentEditTripType() {
        const active = $(".flight-edit-trip.active");
        return active ? active.dataset.editTrip : "oneway";
    }

    function setEditTripType(tripType) {
        $$(".flight-edit-trip").forEach(function (button) {
            button.classList.toggle("active", button.dataset.editTrip === tripType);
        });
        const single = $("#flight-edit-single-fields");
        const multi = $("#flight-edit-multicity-fields");
        const returnWrap = $("#flight-edit-return-wrap");
        if (tripType === "multicity") {
            hide(single);
            show(multi);
            renderEditSegments();
        } else {
            show(single);
            hide(multi);
            if (returnWrap) returnWrap.classList.toggle("hidden", tripType !== "roundtrip");
        }
    }

    function editSegmentsFromSearch() {
        if (searchRequest && Array.isArray(searchRequest.segments) && searchRequest.segments.length) {
            return searchRequest.segments.map(function (segment) {
                return {
                    origin: segment.origin || "",
                    destination: segment.destination || "",
                    departure_date: segment.departure_date || ""
                };
            });
        }
        if (searchRequest && searchRequest.origin) {
            return [{
                origin: searchRequest.origin,
                destination: searchRequest.destination || "",
                departure_date: searchRequest.departure_date || ""
            }];
        }
        return [{origin: "", destination: "", departure_date: ""}, {origin: "", destination: "", departure_date: ""}];
    }

    function renderEditSegments() {
        const container = $("#flight-edit-segments");
        if (!container) return;
        const existing = Array.from(container.querySelectorAll(".flight-edit-segment")).map(function (row) {
            return {
                origin: row.querySelector("[data-segment-origin]")?.value || "",
                destination: row.querySelector("[data-segment-destination]")?.value || "",
                departure_date: row.querySelector("[data-segment-date]")?.value || ""
            };
        });
        const segments = existing.length ? existing : editSegmentsFromSearch();
        container.innerHTML = "";
        segments.forEach(function (segment, index) {
            const row = document.createElement("div");
            row.className = "flight-edit-segment";
            row.innerHTML =
                '<div class="flight-edit-segment-title"><strong>Segment ' + (index + 1) + '</strong>' +
                (segments.length > 2 ? '<button type="button" class="flight-edit-remove" data-remove-segment>Remove</button>' : '') + '</div>' +
                '<label><span>From</span><input data-segment-origin list="flight-edit-airports" value="' + escapeHtml(segment.origin) + '" required></label>' +
                '<label><span>To</span><input data-segment-destination list="flight-edit-airports" value="' + escapeHtml(segment.destination) + '" required></label>' +
                '<label><span>Date</span><input data-segment-date type="date" value="' + escapeHtml(segment.departure_date) + '" required></label>';
            const remove = row.querySelector("[data-remove-segment]");
            if (remove) remove.addEventListener("click", function () { row.remove(); renumberEditSegments(); });
            container.appendChild(row);
        });
        renumberEditSegments();
    }

    function renumberEditSegments() {
        $$("#flight-edit-segments .flight-edit-segment").forEach(function (row, index) {
            const title = row.querySelector(".flight-edit-segment-title strong");
            if (title) title.textContent = "Segment " + (index + 1);
            const remove = row.querySelector("[data-remove-segment]");
            if (remove) remove.classList.toggle("hidden", $$("#flight-edit-segments .flight-edit-segment").length <= 2);
        });
    }

    function openEditSearch() {
        const modal = $("#flight-edit-modal");
        if (!modal) return;
        populateEditAirports();
        const type = searchRequest?.trip_type || "oneway";
        setEditTripType(type);
        if (type !== "multicity") {
            $("#flight-edit-origin").value = searchRequest?.origin || "";
            $("#flight-edit-destination").value = searchRequest?.destination || "";
            $("#flight-edit-departure").value = searchRequest?.departure_date || "";
            $("#flight-edit-return").value = searchRequest?.return_date || "";
        }
        $("#flight-edit-adults").value = searchRequest?.adults ?? 1;
        $("#flight-edit-children").value = searchRequest?.children ?? 0;
        $("#flight-edit-infants").value = searchRequest?.infants ?? 0;
        $("#flight-edit-cabin").value = searchRequest?.cabin_class || "economy";
        hide($("#flight-edit-error"));
        show(modal);
        modal.setAttribute("aria-hidden", "false");
        document.body.classList.add("flight-edit-open");
    }

    function closeEditSearch() {
        const modal = $("#flight-edit-modal");
        if (!modal) return;
        hide(modal);
        modal.setAttribute("aria-hidden", "true");
        document.body.classList.remove("flight-edit-open");
    }

    function buildEditSearchUrl() {
        const type = currentEditTripType();
        const params = new URLSearchParams();
        params.set("trip_type", type);
        params.set("adults", $("#flight-edit-adults").value || "1");
        params.set("children", $("#flight-edit-children").value || "0");
        params.set("infants", $("#flight-edit-infants").value || "0");
        params.set("cabin_class", $("#flight-edit-cabin").value || "economy");
        params.set("special_fare", searchRequest?.special_fare || "regular");
        if (type === "multicity") {
            const segments = $$("#flight-edit-segments .flight-edit-segment").map(function (row) {
                return {
                    origin: row.querySelector("[data-segment-origin]").value.trim().toUpperCase(),
                    destination: row.querySelector("[data-segment-destination]").value.trim().toUpperCase(),
                    departure_date: row.querySelector("[data-segment-date]").value
                };
            });
            params.set("segments", JSON.stringify(segments));
        } else {
            params.set("origin", $("#flight-edit-origin").value.trim().toUpperCase());
            params.set("destination", $("#flight-edit-destination").value.trim().toUpperCase());
            params.set("departure_date", $("#flight-edit-departure").value);
            if (type === "roundtrip") params.set("return_date", $("#flight-edit-return").value);
        }
        return "/flight/results/?" + params.toString();
    }

    function submitEditSearch(event) {
        event.preventDefault();
        const error = $("#flight-edit-error");
        const type = currentEditTripType();
        const adults = Number($("#flight-edit-adults").value);
        const children = Number($("#flight-edit-children").value);
        const infants = Number($("#flight-edit-infants").value);
        let message = "";
        if (adults < 1 || adults > 9) message = "Adults must be between 1 and 9.";
        else if (children < 0 || children > 9) message = "Children must be between 0 and 9.";
        else if (infants < 0 || infants > adults) message = "Infants cannot exceed the number of adults.";
        else if (type === "roundtrip" && !$("#flight-edit-return").value) message = "Please choose a return date.";
        if (type === "multicity" && $$("#flight-edit-segments .flight-edit-segment").length < 2) message = "Add at least two journey segments.";
        if (message) {
            error.textContent = message;
            show(error);
            return;
        }
        window.location.href = buildEditSearchUrl();
    }

    function bindEditSearch() {
        const openButton = $("#flight-edit-search-button");
        if (openButton) openButton.addEventListener("click", openEditSearch);
        $$('[data-edit-modal-close]').forEach(function (element) { element.addEventListener("click", closeEditSearch); });
        $$(".flight-edit-trip").forEach(function (button) {
            button.addEventListener("click", function () { setEditTripType(button.dataset.editTrip); });
        });
        const add = $("#flight-edit-add-segment");
        if (add) add.addEventListener("click", function () {
            const container = $("#flight-edit-segments");
            if (!container || $$("#flight-edit-segments .flight-edit-segment").length >= 6) return;
            const row = document.createElement("div");
            row.className = "flight-edit-segment";
            row.innerHTML = '<div class="flight-edit-segment-title"><strong>Segment</strong><button type="button" class="flight-edit-remove" data-remove-segment>Remove</button></div>' +
                '<label><span>From</span><input data-segment-origin list="flight-edit-airports" required></label>' +
                '<label><span>To</span><input data-segment-destination list="flight-edit-airports" required></label>' +
                '<label><span>Date</span><input data-segment-date type="date" required></label>';
            row.querySelector("[data-remove-segment]").addEventListener("click", function () { row.remove(); renumberEditSegments(); });
            container.appendChild(row);
            renumberEditSegments();
        });
        const form = $("#flight-edit-form");
        if (form) form.addEventListener("submit", submitEditSearch);
    }

    function bindClearFilters() {
        const clearButton = $("#flight-filters-clear");
        if (!clearButton) return;
        clearButton.addEventListener("click", function () {
            activeStopsFilter.clear(); activeAirlineFilter.clear(); activeDepartureFilter.clear(); activeArrivalFilter.clear(); activeBaggageFilter.clear();
            refundableOnly = false;
            const values = allFlights.map(cheapestFare).filter(Boolean).map(function (f) { return f.total_fare; }).filter(function (v) { return typeof v === "number"; });
            maxPrice = values.length ? Math.max.apply(null, values) : null;
            renderFilters(allFlights);
            updatePriceFilterBounds(allFlights);
            applyFiltersAndSort();
        });
    }

    function bindSortControls() {
        const select = $("#flight-sort-select");
        if (select) select.addEventListener("change", function () { activeSort = select.value; updateQuickSortState(); applyFiltersAndSort(); });
        $$('[data-quick-sort]').forEach(function (button) {
            button.addEventListener("click", function () {
                activeSort = button.dataset.quickSort;
                if (select) select.value = activeSort;
                updateQuickSortState();
                applyFiltersAndSort();
            });
        });
    }

    function updateQuickSortState() {
        $$('[data-quick-sort]').forEach(function (button) { button.classList.toggle("active", button.dataset.quickSort === activeSort); });
    }

    function sortFlights(flights) {
        const sorted = flights.slice();
        if (activeSort === "price_asc") sorted.sort(function (a, b) { return (cheapestFare(a)?.total_fare ?? Infinity) - (cheapestFare(b)?.total_fare ?? Infinity); });
        else if (activeSort === "duration_asc") sorted.sort(function (a, b) { return (a.total_duration_minutes ?? Infinity) - (b.total_duration_minutes ?? Infinity); });
        else if (activeSort === "departure_asc") sorted.sort(function (a, b) { return String(a.segments?.[0]?.departure_time || "").localeCompare(String(b.segments?.[0]?.departure_time || "")); });
        else if (activeSort === "arrival_asc") sorted.sort(function (a, b) { return String(a.segments?.[a.segments.length - 1]?.arrival_time || "").localeCompare(String(b.segments?.[b.segments.length - 1]?.arrival_time || "")); });
        return sorted;
    }

    function matchesFilters(flight) {
        if (activeStopsFilter.size && !activeStopsFilter.has(String(Math.min(flight.stops || 0, 2)))) return false;
        if (activeAirlineFilter.size) {
            const codes = (flight.segments || []).map(function (s) { return s.airline_code; });
            if (!codes.some(function (code) { return activeAirlineFilter.has(code); })) return false;
        }
        const first = flight.segments?.[0] || {};
        const last = flight.segments?.[flight.segments.length - 1] || {};
        if (activeDepartureFilter.size && !activeDepartureFilter.has(timeBucket(first.departure_time))) return false;
        if (activeArrivalFilter.size && !activeArrivalFilter.has(timeBucket(last.arrival_time))) return false;
        const fare = cheapestFare(flight);
        if (maxPrice !== null && fare && typeof fare.total_fare === "number" && fare.total_fare > maxPrice) return false;
        if (maxPrice !== null && !fare) return false;
        if (activeBaggageFilter.size) {
            if (!fare || !fare.baggage) return false;
            for (const type of activeBaggageFilter) if (!fare.baggage[type]) return false;
        }
        if (refundableOnly && (!fare || fare.refundable !== true)) return false;
        return true;
    }

    function applyFiltersAndSort() {
        const filtered = sortFlights(allFlights.filter(matchesFilters));
        renderQuickSortSummary(filtered.length ? filtered : allFlights);
        visibleFlightCount = RESULTS_PAGE_SIZE;
        renderFlightList(filtered);
        updateFilterCount(filtered.length);
    }

    function updateFilterCount(count) {
        const el = $("#flight-filter-result-count");
        if (el) el.textContent = count + " option" + (count === 1 ? "" : "s") + " shown";
    }

    function renderQuickSortSummary(flights) {
        const fares = flights.map(cheapestFare).filter(Boolean);
        const cheapest = fares.slice().sort(function (a, b) { return a.total_fare - b.total_fare; })[0];
        const fastest = flights.slice().sort(function (a, b) { return (a.total_duration_minutes || Infinity) - (b.total_duration_minutes || Infinity); })[0];
        if (cheapest) $("#flight-quick-sort-cheapest").textContent = formatPrice(cheapest.total_fare, cheapest.currency);
        if (fastest && typeof fastest.total_duration_minutes === "number") $("#flight-quick-sort-fastest").textContent = formatDuration(fastest.total_duration_minutes);
        $("#flight-quick-sort-recommended").textContent = flights.length + " option" + (flights.length === 1 ? "" : "s");
    }

    function renderFlightList(flights) {
        const container = $("#flight-results-list");
        container.innerHTML = "";
        if (!flights.length) {
            const empty = document.createElement("div");
            empty.className = "bg-white rounded-2xl border border-border p-8 text-center";
            empty.innerHTML = '<i class="fa-solid fa-filter-circle-xmark text-slate-400 text-2xl"></i><p class="font-bold mt-3">No flights match your filters</p><p class="text-sm text-text-secondary mt-1">Try clearing one or more filters.</p><button type="button" id="flight-inline-clear" class="mt-4 text-primary font-bold text-sm">Clear filters</button>';
            container.appendChild(empty);
            $("#flight-inline-clear").addEventListener("click", function () { $("#flight-filters-clear").click(); });
            return;
        }

        const legLabels = Array.from(new Set(flights.map(legLabel)));
        const multiLeg = legLabels.length > 1;
        let renderedCount = 0;
        legLabels.forEach(function (label) {
            const legFlights = flights.filter(function (flight) { return legLabel(flight) === label; });
            const remaining = Math.max(visibleFlightCount - renderedCount, 0);
            const visibleLegFlights = legFlights.slice(0, remaining);
            renderedCount += visibleLegFlights.length;
            if (multiLeg) {
                const heading = document.createElement("div");
                heading.className = "flex items-center justify-between mt-6 mb-3 first:mt-0";
                const title = document.createElement("h3");
                title.className = "text-sm font-bold text-text-secondary uppercase tracking-wide";
                title.textContent = friendlyLegLabel(label) + " options";
                heading.appendChild(title);
                container.appendChild(heading);
            }
            visibleLegFlights.forEach(function (flight) { container.appendChild(buildFlightCard(flight)); });
        });

        if (renderedCount < flights.length) {
            const sentinel = document.createElement("div");
            sentinel.id = "flight-results-scroll-sentinel";
            sentinel.className = "py-8 text-center text-xs text-text-secondary";
            sentinel.textContent = "Scroll for more flights…";
            container.appendChild(sentinel);
            observeResultsSentinel(sentinel, flights);
        } else if (flights.length > RESULTS_PAGE_SIZE) {
            const done = document.createElement("div");
            done.className = "py-8 text-center text-xs text-text-secondary";
            done.textContent = "All available flight options are shown.";
            container.appendChild(done);
        }
    }

    let resultsObserver = null;
    function observeResultsSentinel(sentinel, flights) {
        if (resultsObserver) resultsObserver.disconnect();
        resultsObserver = new IntersectionObserver(function (entries) {
            if (!entries[0].isIntersecting) return;
            resultsObserver.disconnect();
            visibleFlightCount += RESULTS_PAGE_SIZE;
            renderFlightList(flights);
        }, { rootMargin: "700px" });
        resultsObserver.observe(sentinel);
    }

    function friendlyLegLabel(label) {
        const upper = String(label).toUpperCase();
        if (upper === "ONWARD" || upper === "OUTBOUND") return "Outbound";
        if (upper === "RETURN" || upper === "INWARD" || upper === "BACKWARD") return "Return";
        return String(label).replace(/_/g, " ");
    }

    function buildFlightCard(flight) {
        const template = $("#flight-card-template");
        const card = template.content.cloneNode(true);
        const root = card.firstElementChild;
        const firstSegment = flight.segments?.[0] || {};
        const lastSegment = flight.segments?.[flight.segments.length - 1] || {};
        const fare = cheapestFare(flight);
        const key = flightKey(flight);

        root.dataset.flightKey = key;
        if (selectedFlights.has(legLabel(flight)) && flightKey(selectedFlights.get(legLabel(flight))) === key) root.classList.add("ring-2", "ring-primary");

        setText(card, ".js-airline-code", firstSegment.airline_code);
        setText(card, ".js-airline-name", firstSegment.airline_name);
        setText(card, ".js-flight-number", [firstSegment.airline_code, firstSegment.flight_number].filter(Boolean).join(" "));
        setText(card, ".js-departure-time", formatClock(firstSegment.departure_time));
        setText(card, ".js-origin-code", firstSegment.origin);
        setText(card, ".js-origin-city", firstSegment.origin_city);
        setText(card, ".js-arrival-time", formatClock(lastSegment.arrival_time));
        setText(card, ".js-destination-code", lastSegment.destination);
        setText(card, ".js-destination-city", lastSegment.destination_city);
        setText(card, ".js-duration", formatDuration(flight.total_duration_minutes));
        const stops = flight.stops || 0;
        setText(card, ".js-stops-label", stops === 0 ? "Non-stop" : stops + " stop" + (stops === 1 ? "" : "s"));
        setText(card, ".js-stops-note", stops === 0 ? "Direct flight" : "Connecting flight");

        if (fare) {
            setText(card, ".js-price", formatPrice(fare.total_fare, fare.currency));
            setText(card, ".js-fare-type", fare.fare_type || "Standard fare");
            if (fare.baggage && (fare.baggage.checkin || fare.baggage.cabin)) setText(card, ".js-baggage-text", [fare.baggage.checkin, fare.baggage.cabin].filter(Boolean).join(" + cabin "));
            else hideEl(card, ".js-baggage-row");
            if (typeof fare.seats_available === "number") setText(card, ".js-seats-text", fare.seats_available + " seats left"); else hideEl(card, ".js-seats-row");
        } else {
            setText(card, ".js-price", "Price on request");
            hideEl(card, ".js-baggage-row"); hideEl(card, ".js-fare-type-row"); hideEl(card, ".js-seats-row");
        }

        const button = card.querySelector(".js-select-flight");
        if (button) {
            const isSelected = selectedFlights.has(legLabel(flight)) && flightKey(selectedFlights.get(legLabel(flight))) === key;
            button.textContent = isSelected ? "SELECTED · CHOOSE FARE" : "SELECT FLIGHT";
            button.addEventListener("click", function () { selectFlight(flight); });
        }
        const detailsButton = card.querySelector(".js-flight-details");
        const details = card.querySelector(".js-flight-details-panel");
        if (detailsButton && details) detailsButton.addEventListener("click", function () { details.classList.toggle("hidden"); detailsButton.textContent = details.classList.contains("hidden") ? "Flight details" : "Hide details"; });

        const segmentList = card.querySelector(".js-segment-list");
        if (segmentList) {
            (flight.segments || []).forEach(function (segment, index) {
                const row = document.createElement("div");
                row.className = "py-3 border-b border-border last:border-b-0 text-xs";
                row.innerHTML = '<div class="font-bold">' + escapeHtml(formatClock(segment.departure_time)) + ' ' + escapeHtml(segment.origin || "") + ' → ' + escapeHtml(formatClock(segment.arrival_time)) + ' ' + escapeHtml(segment.destination || "") + '</div><div class="text-text-secondary mt-1">' + escapeHtml(segment.airline_name || segment.airline_code || "") + ' · ' + escapeHtml([segment.airline_code, segment.flight_number].filter(Boolean).join(" ")) + ' · ' + escapeHtml(formatDuration(segment.duration_minutes)) + (index < flight.segments.length - 1 ? " · connection" : "") + '</div>';
                segmentList.appendChild(row);
            });
        }
        return card;
    }

    function selectFlight(flight) {
        selectedFlights.set(legLabel(flight), flight);
        const fare = cheapestFare(flight);
        if (fare && fare.fare_id) {
            selectedFares.set(legLabel(flight), fare);
        } else {
            selectedFares.delete(legLabel(flight));
        }

        renderFlightList(sortFlights(allFlights.filter(matchesFilters)));
        updateSelectionPanel();

        const requiredLegs = Array.from(new Set(allFlights.map(legLabel)));
        if (requiredLegs.every(function (leg) { return selectedFlights.has(leg); })) {
            openFareModal();
        } else {
            showError("selection_pending", "Select a flight for each journey leg to continue.");
        }
    }

    function getFareFeatures(fare) {
        const features = [];
        if (fare.baggage && fare.baggage.checkin) features.push({ icon: "fa-suitcase-rolling", text: "Check-in " + fare.baggage.checkin });
        if (fare.baggage && fare.baggage.cabin) features.push({ icon: "fa-briefcase", text: "Cabin " + fare.baggage.cabin });
        if (fare.meal_included === true) features.push({ icon: "fa-utensils", text: "Meal included" });
        if (fare.refundable === true) features.push({ icon: "fa-rotate-left", text: "Refundable" });
        if (typeof fare.seats_available === "number") features.push({ icon: "fa-chair", text: fare.seats_available + " seats left" });
        return features;
    }

    function renderFareModal() {
        const body = $("#flight-fare-modal-body");
        const total = $("#flight-fare-modal-total");
        const continueButton = $("#flight-fare-modal-continue");
        const error = $("#flight-fare-modal-error");
        if (!body || !total || !continueButton) return;

        body.innerHTML = "";
        if (error) {
            error.textContent = "";
            hide(error);
        }

        let totalFare = 0;
        let complete = true;

        Array.from(selectedFlights.entries()).forEach(function (entry) {
            const leg = entry[0];
            const flight = entry[1];
            const fares = (flight.fares || []).filter(function (fare) { return fare && fare.fare_id; });
            const currentFare = selectedFares.get(leg);
            const section = document.createElement("section");
            section.className = "fare-modal-leg";

            const first = (flight.segments || [])[0] || {};
            const last = (flight.segments || [])[flight.segments.length - 1] || first;

            section.innerHTML =
                '<div class="fare-modal-leg-head">' +
                    '<div><span class="fare-modal-leg-label">' + escapeHtml(friendlyLegLabel(leg)) + '</span>' +
                    '<strong>' + escapeHtml(first.origin || "") + ' → ' + escapeHtml(last.destination || "") + '</strong></div>' +
                    '<span class="fare-modal-flight-meta">' + escapeHtml([first.airline_name || first.airline_code, first.flight_number].filter(Boolean).join(" · ")) + '</span>' +
                '</div>';

            const options = document.createElement("div");
            options.className = "fare-modal-options";

            if (!fares.length) {
                complete = false;
                options.innerHTML = '<div class="fare-modal-empty">Fare options are not available for this flight.</div>';
            }

            fares.forEach(function (fare) {
                const option = document.createElement("button");
                option.type = "button";
                option.className = "fare-modal-option" + (currentFare && currentFare.fare_id === fare.fare_id ? " is-selected" : "");
                const features = getFareFeatures(fare);
                const featureHtml = features.length
                    ? '<div class="fare-modal-features">' + features.map(function (item) {
                        return '<span><i class="fa-solid ' + item.icon + '"></i>' + escapeHtml(item.text) + '</span>';
                    }).join("") + '</div>'
                    : '<div class="fare-modal-features"><span><i class="fa-solid fa-circle-info"></i> Fare details provided by airline</span></div>';

                option.innerHTML =
                    '<div class="fare-modal-option-top">' +
                        '<div><span class="fare-modal-radio"></span><strong>' + escapeHtml(fare.fare_type || fare.cabin_class || "Fare") + '</strong>' +
                        (fare.booking_class ? '<span class="fare-modal-class">' + escapeHtml(fare.booking_class) + '</span>' : '') + '</div>' +
                        '<strong class="fare-modal-price">' + escapeHtml(formatPrice(fare.total_fare, fare.currency)) + '</strong>' +
                    '</div>' +
                    featureHtml;

                option.addEventListener("click", function () {
                    selectedFares.set(leg, fare);
                    renderFareModal();
                });
                options.appendChild(option);
            });

            section.appendChild(options);
            body.appendChild(section);

            const chosen = selectedFares.get(leg);
            if (!chosen || !chosen.fare_id) {
                complete = false;
            } else if (typeof chosen.total_fare === "number") {
                totalFare += chosen.total_fare;
            }
        });

        total.textContent = totalFare ? formatPrice(totalFare, "₹") : "—";
        continueButton.disabled = !complete;
        continueButton.classList.toggle("is-disabled", !complete);
    }

    function openFareModal() {
        const modal = $("#flight-fare-modal");
        if (!modal) return;
        fareModalFlightKey = "selection";
        renderFareModal();
        show(modal);
        modal.setAttribute("aria-hidden", "false");
        document.body.classList.add("fare-modal-open");
    }

    function closeFareModal() {
        const modal = $("#flight-fare-modal");
        if (!modal) return;
        hide(modal);
        modal.setAttribute("aria-hidden", "true");
        document.body.classList.remove("fare-modal-open");
        fareModalFlightKey = null;
    }

    function submitFareSelection() {
        const requiredLegs = Array.from(new Set(allFlights.map(legLabel)));
        if (!requiredLegs.every(function (leg) { return selectedFlights.has(leg) && selectedFares.has(leg); })) {
            return;
        }

        const button = $("#flight-fare-modal-continue");
        const error = $("#flight-fare-modal-error");
        if (!button) return;

        button.disabled = true;
        button.textContent = "Checking fare…";
        if (error) hide(error);

        const selected = requiredLegs.map(function (leg) {
            return selectedFlights.get(leg);
        });
        const priceIds = requiredLegs.map(function (leg) {
            return selectedFares.get(leg).fare_id;
        });

        fetch("/api/v1/flights/selection/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": getCsrfToken() },
            body: JSON.stringify({ selected: selected, search_request: searchRequest })
        })
            .then(function (response) {
                return response.json().then(function (data) { return { status: response.status, data: data }; });
            })
            .then(function (result) {
                if (result.status !== 200 || !result.data.success) {
                    throw new Error(result.data.error_message || "Could not save your flight selection.");
                }

                return fetch("/api/v1/flights/review/", {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-CSRFToken": getCsrfToken() },
                    body: JSON.stringify({ price_ids: priceIds })
                });
            })
            .then(function (response) {
                return response.json().then(function (data) { return { status: response.status, data: data }; });
            })
            .then(function (result) {
                if (result.status !== 200 || !result.data.success) {
                    throw new Error(result.data.error_message || "The fare could not be confirmed. Please choose another option.");
                }
                window.location.href = "/flight/traveller/";
            })
            .catch(function (err) {
                button.disabled = false;
                button.textContent = "Continue to traveller details";
                if (error) {
                    error.textContent = err.message;
                    show(error);
                }
            });
    }

    function bindSelectionPanel() {
        updateSelectionPanel();
        const button = $("#flight-selection-continue");
        if (button && !button.dataset.bound) {
            button.dataset.bound = "1";
            button.addEventListener("click", function () {
                const requiredLegs = Array.from(new Set(allFlights.map(legLabel)));
                if (!requiredLegs.every(function (leg) { return selectedFlights.has(leg); })) return;
                button.disabled = true;
                const payload = {
                    selected: Array.from(selectedFlights.values()),
                    search_request: searchRequest
                };
                fetch("/api/v1/flights/selection/", {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-CSRFToken": getCsrfToken() },
                    body: JSON.stringify(payload)
                }).then(function (response) {
                    return response.json().then(function (data) { return { status: response.status, data: data }; });
                }).then(function (result) {
                    if (result.status === 200 && result.data.success) {
                        window.location.href = result.data.redirect_url;
                        return;
                    }
                    throw new Error(result.data.error_message || "Could not save your selection.");
                }).catch(function (error) {
                    button.disabled = false;
                    showError("selection_error", error.message);
                });
            });
        }
    }

    function updateSelectionPanel() {
        const panel = $("#flight-selection-panel");
        if (!panel) return;
        const requiredLegs = Array.from(new Set(allFlights.map(legLabel)));
        const selected = requiredLegs.filter(function (leg) { return selectedFlights.has(leg); });
        if (!selected.length) { hide(panel); return; }
        show(panel);
        const list = $("#flight-selection-list");
        list.innerHTML = "";
        selected.forEach(function (leg) {
            const flight = selectedFlights.get(leg);
            const segment = flight.segments?.[0] || {};
            const last = flight.segments?.[flight.segments.length - 1] || {};
            const fare = cheapestFare(flight);
            const item = document.createElement("div");
            item.className = "flex items-center justify-between gap-3 py-2 border-b border-border last:border-0";
            item.innerHTML = '<div><p class="text-[10px] font-bold uppercase text-text-secondary">' + escapeHtml(friendlyLegLabel(leg)) + '</p><p class="text-sm font-bold mt-0.5">' + escapeHtml(segment.origin || "") + ' → ' + escapeHtml(last.destination || "") + ' · ' + escapeHtml(formatClock(segment.departure_time)) + '</p></div><div class="text-right"><p class="font-extrabold">' + escapeHtml(fare ? formatPrice(fare.total_fare, fare.currency) : "—") + '</p><button type="button" class="text-[11px] text-danger font-semibold js-remove-selected">Remove</button></div>';
            item.querySelector(".js-remove-selected").addEventListener("click", function () { selectedFlights.delete(leg); selectedFares.delete(leg); updateSelectionPanel(); renderFlightList(sortFlights(allFlights.filter(matchesFilters))); });
            list.appendChild(item);
        });
        const ready = selected.length === requiredLegs.length;
        $("#flight-selection-progress").textContent = selected.length + " of " + requiredLegs.length + " journey leg" + (requiredLegs.length === 1 ? "" : "s") + " selected";
        const button = $("#flight-selection-continue");
        if (button) { button.disabled = !ready; button.classList.toggle("opacity-50", !ready); button.classList.toggle("cursor-not-allowed", !ready); button.textContent = ready ? "CONTINUE TO FARE REVIEW" : "SELECT ALL LEGS"; }
    }

    function setText(root, selector, value) { const el = root.querySelector(selector); if (el) el.textContent = value || ""; }
    function hideEl(root, selector) { const el = root.querySelector(selector); if (el) el.classList.add("hidden"); }
    function escapeHtml(value) { return String(value ?? "").replace(/[&<>\"']/g, function (c) { return ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;", "'":"&#39;"})[c]; }); }

    function getCsrfToken() {
        const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : "";
    }

    function bindMobileFilters() {
        const toggle = $("#flight-filters-toggle");
        const sidebar = $("#flight-filters-sidebar");
        if (!toggle || !sidebar) return;
        toggle.addEventListener("click", function () { sidebar.classList.toggle("hidden"); });
    }

    function initialize() {
        bindClearFilters();
        bindSortControls();
        bindMobileFilters();
        bindEditSearch();
        $$("[data-fare-modal-close]").forEach(function (element) {
            element.addEventListener("click", closeFareModal);
        });
        const fareContinue = $("#flight-fare-modal-continue");
        if (fareContinue) fareContinue.addEventListener("click", submitFareSelection);
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") {
                closeFareModal();
                closeEditSearch();
            }
        });
        runSearch();
    }

    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize, { once: true });
    else initialize();
})();
