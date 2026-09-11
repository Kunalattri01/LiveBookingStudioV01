/* ================================================================
   MULTI CITY SEARCH

   Adds/removes flight segment rows (min 2, max 6), each with its own
   From/To (backed by our own /flight/airports/ master-data endpoint -
   never TripJack) and departure date. Exposes window.MultiCitySearch
   so flight-search.js can validate and build the search URL for
   multicity without needing to know about this module's internals.
   ================================================================ */

(function () {

    "use strict";

    if (window.__MULTICITY_SEARCH_INITIALIZED__) {
        return;
    }

    window.__MULTICITY_SEARCH_INITIALIZED__ = true;

    const MIN_SEGMENTS = 2;
    const MAX_SEGMENTS = 6;

    let rows = []; // { element, origin: {code, city, airport}|null, destination: {...}|null }
    let initialized = false;


    function $(selector, root) {
        return (root || document).querySelector(selector);
    }

    function $$(selector, root) {
        return Array.from((root || document).querySelectorAll(selector));
    }


    function fetchAirports(query) {
        return fetch("/flight/airports/?q=" + encodeURIComponent(query || ""))
            .then(function (response) {
                if (!response.ok) throw new Error("airport search failed");
                return response.json();
            })
            .then(function (data) {
                return (data && data.results) || [];
            })
            .catch(function () {
                return [];
            });
    }


    function createRow(index) {
        const template = $("#multicity-segment-template");
        const fragment = template.content.cloneNode(true);
        const rowEl = fragment.querySelector("[data-segment-row]");

        const row = { element: rowEl, origin: null, destination: null };

        const originInput = rowEl.querySelector('[data-mc-field="origin"]');
        const destinationInput = rowEl.querySelector('[data-mc-field="destination"]');
        const dateInput = rowEl.querySelector('[data-mc-field="date"]');
        const originList = rowEl.querySelector('[data-mc-list="origin"]');
        const destinationList = rowEl.querySelector('[data-mc-list="destination"]');
        const removeButton = rowEl.querySelector(".mc-remove-segment");

        dateInput.min = new Date().toISOString().slice(0, 10);

        bindAirportField(originInput, originList, function (airport) {
            row.origin = airport;
        });

        bindAirportField(destinationInput, destinationList, function (airport) {
            row.destination = airport;
        });

        removeButton.addEventListener("click", function () {
            removeRow(row);
        });

        $("#multicity-segment-list").appendChild(rowEl);
        rows.splice(index, 0, row);
        updateRemoveButtonsVisibility();

        return row;
    }


    function bindAirportField(input, listEl, onSelect) {
        let debounceTimer = null;

        input.addEventListener("input", function () {
            const query = input.value.trim();

            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(function () {
                fetchAirports(query).then(function (results) {
                    renderAirportSuggestions(listEl, results, function (airport) {
                        input.value = airport.city + " (" + airport.code + ")";
                        listEl.classList.add("hidden");
                        onSelect(airport);
                    });
                });
            }, 150);
        });

        input.addEventListener("focus", function () {
            fetchAirports(input.value.trim()).then(function (results) {
                renderAirportSuggestions(listEl, results, function (airport) {
                    input.value = airport.city + " (" + airport.code + ")";
                    listEl.classList.add("hidden");
                    onSelect(airport);
                });
            });
        });

        document.addEventListener("click", function (event) {
            if (event.target !== input && !listEl.contains(event.target)) {
                listEl.classList.add("hidden");
            }
        });
    }


    function renderAirportSuggestions(listEl, airports, onPick) {
        listEl.innerHTML = "";

        if (!airports.length) {
            listEl.classList.add("hidden");
            return;
        }

        listEl.className =
            "mc-airport-list absolute z-20 left-0 right-0 mt-1 bg-white border border-border rounded-xl shadow-lg max-h-56 overflow-y-auto";

        airports.forEach(function (airport) {
            const item = document.createElement("button");
            item.type = "button";
            item.className = "w-full text-left px-4 py-2.5 hover:bg-slate-50 flex items-center gap-3 text-sm";
            item.innerHTML =
                '<span class="font-bold text-primary w-10">' + escapeHtml(airport.code) + '</span>' +
                '<span><span class="font-semibold text-text-primary">' + escapeHtml(airport.city) + '</span>' +
                '<span class="block text-xs text-text-secondary">' + escapeHtml(airport.airport) + '</span></span>';

            item.addEventListener("click", function () {
                onPick(airport);
            });

            listEl.appendChild(item);
        });

        listEl.classList.remove("hidden");
    }


    function escapeHtml(value) {
        const div = document.createElement("div");
        div.textContent = value == null ? "" : String(value);
        return div.innerHTML;
    }


    function removeRow(row) {
        if (rows.length <= MIN_SEGMENTS) {
            return;
        }

        row.element.remove();
        rows = rows.filter(function (r) { return r !== row; });
        updateRemoveButtonsVisibility();
    }


    function updateRemoveButtonsVisibility() {
        rows.forEach(function (row) {
            const removeButton = row.element.querySelector(".mc-remove-segment");
            if (rows.length <= MIN_SEGMENTS) {
                removeButton.classList.add("invisible");
            } else {
                removeButton.classList.remove("invisible");
            }
        });

        const addButton = $("#multicity-add-segment");
        if (addButton) {
            addButton.classList.toggle("hidden", rows.length >= MAX_SEGMENTS);
        }
    }


    function ensureInitialized() {
        if (initialized) {
            return;
        }

        initialized = true;

        for (let i = 0; i < MIN_SEGMENTS; i++) {
            createRow(i);
        }

        const addButton = $("#multicity-add-segment");
        if (addButton) {
            addButton.addEventListener("click", function () {
                if (rows.length >= MAX_SEGMENTS) return;
                createRow(rows.length);
            });
        }
    }


    function bindTripTypeToggle() {
        $$('input[name="trip-type"]').forEach(function (radio) {
            radio.addEventListener("change", function () {
                if (!radio.checked) return;

                const singleFields = $("#single-trip-fields");
                const multiFields = $("#multicity-fields");

                if (radio.value === "multicity") {
                    ensureInitialized();
                    if (singleFields) singleFields.classList.add("hidden");
                    if (multiFields) multiFields.classList.remove("hidden");
                } else {
                    if (singleFields) singleFields.classList.remove("hidden");
                    if (multiFields) multiFields.classList.add("hidden");
                }
            });
        });
    }


    function getSegments() {
        return rows
            .filter(function (row) { return row.origin && row.destination; })
            .map(function (row) {
                const dateInput = row.element.querySelector('[data-mc-field="date"]');
                return {
                    origin: row.origin.code,
                    destination: row.destination.code,
                    departure_date: dateInput.value
                };
            });
    }


    function validate() {
        const filledRows = rows.filter(function (row) {
            const dateInput = row.element.querySelector('[data-mc-field="date"]');
            return row.origin || row.destination || (dateInput && dateInput.value);
        });

        if (filledRows.length < MIN_SEGMENTS) {
            return "Please add at least " + MIN_SEGMENTS + " flights for multi-city search.";
        }

        for (let i = 0; i < rows.length; i++) {
            const row = rows[i];
            const dateInput = row.element.querySelector('[data-mc-field="date"]');

            if (!row.origin || !row.destination || !dateInput.value) {
                return "Please complete From, To, and Date for flight " + (i + 1) + ".";
            }

            if (row.origin.code === row.destination.code) {
                return "From and To cannot be the same for flight " + (i + 1) + ".";
            }
        }

        for (let i = 1; i < rows.length; i++) {
            const prevDate = rows[i - 1].element.querySelector('[data-mc-field="date"]').value;
            const currentDate = rows[i].element.querySelector('[data-mc-field="date"]').value;

            if (currentDate < prevDate) {
                return "Flight " + (i + 1) + " date cannot be before flight " + i + "'s date.";
            }
        }

        return "";
    }


    window.MultiCitySearch = {
        getSegments: getSegments,
        validate: validate
    };


    function initializeModule() {
        bindTripTypeToggle();
    }


    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initializeModule, { once: true });
    } else {
        initializeModule();
    }

})();
