/* ================================================================
   HOMEPAGE HOTEL SEARCH

   Collects destination / check-in / check-out / guests & rooms from
   the existing homepage hotel panel and submits them to our backend
   for validation. Does not call any hotel provider — no live hotel
   data exists yet, so this intentionally stops at "search received".
   ================================================================ */

(function () {

    "use strict";

    if (window.__SEA_OF_SEATS_HOTEL_SEARCH_INITIALIZED__) {
        return;
    }

    window.__SEA_OF_SEATS_HOTEL_SEARCH_INITIALIZED__ = true;


    function $(selector) {
        return document.querySelector(selector);
    }


    function injectDestSuggestionStyles() {

        if (document.getElementById("hotel-dest-suggestion-styles")) {
            return;
        }

        var style = document.createElement("style");
        style.id = "hotel-dest-suggestion-styles";
        style.textContent =
            ".hds-list{position:absolute;z-index:50;background:#fff;border:1px solid #e2e8f0;border-radius:12px;" +
            "margin-top:4px;box-shadow:0 10px 30px rgba(15,23,42,.12);min-width:280px;max-width:360px;" +
            "max-height:360px;overflow-y:auto;padding:6px 0;}" +
            ".hds-section{padding:8px 14px 4px;font-size:11px;font-weight:700;letter-spacing:.04em;" +
            "text-transform:uppercase;color:#94a3b8;}" +
            ".hds-row{display:flex;align-items:center;gap:10px;padding:9px 14px;cursor:pointer;}" +
            ".hds-row:hover{background:#f8fafc;}" +
            ".hds-icon{width:18px;flex-shrink:0;color:#0d9488;font-size:13px;text-align:center;}" +
            ".hds-main{display:flex;flex-direction:column;min-width:0;}" +
            ".hds-title{font-size:14px;color:#0f172a;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}" +
            ".hds-title b{font-weight:700;}" +
            ".hds-sub{font-size:12px;color:#64748b;}" +
            ".hds-empty{padding:10px 14px;font-size:13px;color:#64748b;}";
        document.head.appendChild(style);

    }


    function bindDestinationAutocomplete() {

        var input = $("#hotel-dest");

        if (!input) {
            return;
        }

        input.setAttribute("autocomplete", "off");

        injectDestSuggestionStyles();

        var list = document.createElement("div");
        list.id = "hotel-dest-suggestions";
        list.className = "hds-list";
        list.style.display = "none";

        var anchor = input.closest(".search-field") || input.parentElement;
        anchor.style.position = anchor.style.position || "relative";
        anchor.appendChild(list);

        var debounceTimer = null;

        function boldMatch(text, query) {
            if (!query) return escapeHtml(text);
            var idx = text.toLowerCase().indexOf(query.toLowerCase());
            if (idx === -1) return escapeHtml(text);
            return (
                escapeHtml(text.slice(0, idx)) +
                "<b>" + escapeHtml(text.slice(idx, idx + query.length)) + "</b>" +
                escapeHtml(text.slice(idx + query.length))
            );
        }

        function escapeHtml(value) {
            return String(value == null ? "" : value).replace(/[&<>"']/g, function (c) {
                return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c];
            });
        }

        function addSectionLabel(text) {
            var label = document.createElement("div");
            label.className = "hds-section";
            label.textContent = text;
            list.appendChild(label);
        }

        function addCityRow(city, query) {
            var row = document.createElement("div");
            row.className = "hds-row";
            row.innerHTML =
                '<span class="hds-icon"><i class="fa-solid fa-arrow-trend-up" aria-hidden="true"></i></span>' +
                '<span class="hds-main"><span class="hds-title">' + boldMatch(city.city, query) + '</span></span>';
            row.addEventListener("mousedown", function (event) {
                event.preventDefault();
                input.value = city.city;
                list.style.display = "none";
            });
            list.appendChild(row);
        }

        function addHotelRow(hotel, query) {
            var row = document.createElement("div");
            row.className = "hds-row";
            row.innerHTML =
                '<span class="hds-icon"><i class="fa-solid fa-hotel" aria-hidden="true"></i></span>' +
                '<span class="hds-main"><span class="hds-title">' + boldMatch(hotel.name, query) + '</span>' +
                '<span class="hds-sub">Hotel in ' + escapeHtml(hotel.city) + '</span></span>';
            row.addEventListener("mousedown", function (event) {
                event.preventDefault();
                input.value = hotel.name;
                list.style.display = "none";
            });
            list.appendChild(row);
        }

        function renderResults(data, query) {
            list.innerHTML = "";

            var cities = data.cities || [];
            var hotels = data.hotels || [];

            if (!cities.length && !hotels.length) {
                var empty = document.createElement("div");
                empty.className = "hds-empty";
                empty.textContent = "No matching properties in our current catalog.";
                list.appendChild(empty);
                list.style.display = "block";
                return;
            }

            if (cities.length) {
                addSectionLabel(query ? "Cities" : "Popular destinations");
                cities.forEach(function (city) { addCityRow(city, query); });
            }

            if (hotels.length) {
                addSectionLabel("Hotels");
                hotels.forEach(function (hotel) { addHotelRow(hotel, query); });
            }

            list.style.display = "block";
        }

        function runSearch(query) {
            fetch("/api/v1/hotels/destinations/?q=" + encodeURIComponent(query))
                .then(function (response) { return response.json(); })
                .then(function (data) { renderResults(data, query); })
                .catch(function () { list.style.display = "none"; });
        }

        input.addEventListener("input", function () {
            var query = input.value.trim();
            window.clearTimeout(debounceTimer);
            debounceTimer = window.setTimeout(function () { runSearch(query); }, 250);
        });

        // Show suggestions as soon as the field is focused, even before
        // typing anything - an empty query returns our top/popular active
        // destinations, so the list is never empty-and-unhelpful on click.
        input.addEventListener("focus", function () {
            runSearch(input.value.trim());
        });

        document.addEventListener("click", function (event) {
            if (event.target !== input && !list.contains(event.target)) {
                list.style.display = "none";
            }
        });

    }


    var MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    var MONTH_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    var WEEKDAY_SHORT = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];


    function injectDatePickerStyles() {

        if (document.getElementById("hotel-datepicker-styles")) {
            return;
        }

        var style = document.createElement("style");
        style.id = "hotel-datepicker-styles";
        style.textContent =
            "#hotel-daterange-popup{position:absolute;z-index:60;background:#fff;border:1px solid #e2e8f0;border-radius:16px;" +
            "box-shadow:0 20px 45px rgba(15,23,42,.18);padding:18px;display:none;top:100%;margin-top:8px;left:0;}" +
            "#hotel-daterange-popup.open{display:block;}" +
            ".hdr-header{display:flex;align-items:center;gap:10px;padding-bottom:12px;margin-bottom:12px;border-bottom:1px solid #e2e8f0;font-weight:700;color:#0f172a;font-size:15px;}" +
            ".hdr-header .hdr-sep{color:#94a3b8;}" +
            ".hdr-months{display:flex;gap:24px;}" +
            ".hdr-month{width:220px;}" +
            ".hdr-month-title{display:flex;align-items:center;justify-content:space-between;font-weight:700;margin-bottom:8px;}" +
            ".hdr-nav{background:none;border:none;cursor:pointer;color:#0d9488;font-size:16px;padding:4px 8px;}" +
            ".hdr-nav[disabled]{opacity:.25;cursor:not-allowed;}" +
            ".hdr-weekdays{display:grid;grid-template-columns:repeat(7,1fr);font-size:11px;color:#94a3b8;text-align:center;margin-bottom:4px;}" +
            ".hdr-days{display:grid;grid-template-columns:repeat(7,1fr);gap:2px;}" +
            ".hdr-day{text-align:center;font-size:13px;padding:7px 0;border-radius:8px;cursor:pointer;color:#0f172a;}" +
            ".hdr-day.is-empty{cursor:default;}" +
            ".hdr-day.is-disabled{color:#cbd5e1;cursor:not-allowed;}" +
            ".hdr-day.is-today{font-weight:700;text-decoration:underline;}" +
            ".hdr-day.in-range{background:#ecfdf5;border-radius:0;}" +
            ".hdr-day.is-start,.hdr-day.is-end{background:#0d9488;color:#fff;font-weight:700;}" +
            ".hdr-day:not(.is-disabled):not(.is-empty):hover{background:#ccfbf1;}";
        document.head.appendChild(style);

    }


    function startOfDay(date) {
        return new Date(date.getFullYear(), date.getMonth(), date.getDate());
    }


    function isoDate(date) {
        var y = date.getFullYear();
        var m = String(date.getMonth() + 1).padStart(2, "0");
        var d = String(date.getDate()).padStart(2, "0");
        return y + "-" + m + "-" + d;
    }


    function displayDate(date) {
        return date.getDate() + " " + MONTH_SHORT[date.getMonth()] + " " + String(date.getFullYear()).slice(-2);
    }


    function bindDateRangePicker() {

        var checkinInput = $("#hotel-checkin");
        var checkoutInput = $("#hotel-checkout");

        if (!checkinInput || !checkoutInput) {
            return;
        }

        injectDatePickerStyles();

        checkinInput.type = "text";
        checkoutInput.type = "text";
        checkinInput.readOnly = true;
        checkoutInput.readOnly = true;
        checkinInput.autocomplete = "off";
        checkoutInput.autocomplete = "off";

        var anchor = checkinInput.closest(".search-field") || checkinInput.parentElement;
        anchor.style.position = anchor.style.position || "relative";

        var popup = document.createElement("div");
        popup.id = "hotel-daterange-popup";
        anchor.appendChild(popup);

        var today = startOfDay(new Date());
        var viewMonth = new Date(today.getFullYear(), today.getMonth(), 1);
        var rangeStart = null;
        var rangeEnd = null;

        function commitValues() {

            if (rangeStart) {
                checkinInput.value = displayDate(rangeStart);
                checkinInput.dataset.isoDate = isoDate(rangeStart);
            }

            if (rangeEnd) {
                checkoutInput.value = displayDate(rangeEnd);
                checkoutInput.dataset.isoDate = isoDate(rangeEnd);
            } else {
                checkoutInput.value = "";
                delete checkoutInput.dataset.isoDate;
            }

        }

        function buildMonthGrid(monthDate) {

            var wrap = document.createElement("div");
            wrap.className = "hdr-month";

            var title = document.createElement("div");
            title.className = "hdr-month-title";
            title.textContent = MONTH_NAMES[monthDate.getMonth()] + " " + monthDate.getFullYear();
            wrap.appendChild(title);

            var weekdays = document.createElement("div");
            weekdays.className = "hdr-weekdays";
            WEEKDAY_SHORT.forEach(function (w) {
                var cell = document.createElement("div");
                cell.textContent = w;
                weekdays.appendChild(cell);
            });
            wrap.appendChild(weekdays);

            var days = document.createElement("div");
            days.className = "hdr-days";

            var firstOfMonth = new Date(monthDate.getFullYear(), monthDate.getMonth(), 1);
            var leadingBlanks = firstOfMonth.getDay();
            var daysInMonth = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0).getDate();

            for (var i = 0; i < leadingBlanks; i++) {
                var blank = document.createElement("div");
                blank.className = "hdr-day is-empty";
                days.appendChild(blank);
            }

            for (var d = 1; d <= daysInMonth; d++) {
                var cellDate = new Date(monthDate.getFullYear(), monthDate.getMonth(), d);
                var cell = document.createElement("div");
                cell.className = "hdr-day";
                cell.textContent = String(d);

                if (cellDate < today) {
                    cell.classList.add("is-disabled");
                } else {
                    if (cellDate.getTime() === today.getTime()) cell.classList.add("is-today");
                    if (rangeStart && cellDate.getTime() === rangeStart.getTime()) cell.classList.add("is-start");
                    if (rangeEnd && cellDate.getTime() === rangeEnd.getTime()) cell.classList.add("is-end");
                    if (rangeStart && rangeEnd && cellDate > rangeStart && cellDate < rangeEnd) cell.classList.add("in-range");

                    cell.addEventListener("click", function (clicked) {
                        return function (event) {
                            // Re-render replaces this cell's DOM node; stop the
                            // click here so the document-level outside-click
                            // handler doesn't see a detached target and close
                            // the popup right after selecting a date.
                            event.stopPropagation();
                            handleDayClick(clicked);
                        };
                    }(cellDate));
                }

                days.appendChild(cell);
            }

            wrap.appendChild(days);
            return wrap;

        }

        function render() {

            popup.innerHTML = "";

            var header = document.createElement("div");
            header.className = "hdr-header";
            var startLabel = document.createElement("span");
            startLabel.textContent = rangeStart ? displayDate(rangeStart) : "Check-in";
            var sep = document.createElement("span");
            sep.className = "hdr-sep";
            sep.textContent = "—";
            var endLabel = document.createElement("span");
            endLabel.textContent = rangeEnd ? displayDate(rangeEnd) : "Check-out";
            header.appendChild(startLabel);
            header.appendChild(sep);
            header.appendChild(endLabel);
            popup.appendChild(header);

            var months = document.createElement("div");
            months.className = "hdr-months";

            var secondMonth = new Date(viewMonth.getFullYear(), viewMonth.getMonth() + 1, 1);

            var firstMonthWrap = buildMonthGrid(viewMonth);
            var prevButton = document.createElement("button");
            prevButton.type = "button";
            prevButton.className = "hdr-nav";
            prevButton.innerHTML = "&larr;";
            prevButton.disabled = viewMonth.getFullYear() === today.getFullYear() && viewMonth.getMonth() === today.getMonth();
            prevButton.addEventListener("click", function (event) {
                event.stopPropagation();
                viewMonth = new Date(viewMonth.getFullYear(), viewMonth.getMonth() - 1, 1);
                render();
            });
            firstMonthWrap.querySelector(".hdr-month-title").prepend(prevButton);

            var secondMonthWrap = buildMonthGrid(secondMonth);
            var nextButton = document.createElement("button");
            nextButton.type = "button";
            nextButton.className = "hdr-nav";
            nextButton.innerHTML = "&rarr;";
            nextButton.addEventListener("click", function (event) {
                event.stopPropagation();
                viewMonth = new Date(viewMonth.getFullYear(), viewMonth.getMonth() + 1, 1);
                render();
            });
            secondMonthWrap.querySelector(".hdr-month-title").appendChild(nextButton);

            months.appendChild(firstMonthWrap);
            months.appendChild(secondMonthWrap);
            popup.appendChild(months);

        }

        function handleDayClick(date) {

            if (!rangeStart || (rangeStart && rangeEnd)) {
                rangeStart = date;
                rangeEnd = null;
            } else if (date.getTime() > rangeStart.getTime()) {
                rangeEnd = date;
            } else {
                rangeStart = date;
                rangeEnd = null;
            }

            commitValues();
            render();

            if (rangeStart && rangeEnd) {
                closePopup();
            }

        }

        function openPopup() {
            popup.classList.add("open");
            render();
        }

        function closePopup() {
            popup.classList.remove("open");
        }

        checkinInput.addEventListener("click", function (event) {
            event.stopPropagation();
            openPopup();
        });

        checkoutInput.addEventListener("click", function (event) {
            event.stopPropagation();
            openPopup();
        });

        document.addEventListener("click", function (event) {
            if (!popup.contains(event.target) && event.target !== checkinInput && event.target !== checkoutInput) {
                closePopup();
            }
        });

    }


    function parseGuestsAndRooms(optionText) {

        var guestsMatch = /(\d+)\s*Guests?/i.exec(optionText || "");
        var roomsMatch = /(\d+)\s*Rooms?/i.exec(optionText || "");

        return {
            guests: guestsMatch ? parseInt(guestsMatch[1], 10) : 2,
            rooms: roomsMatch ? parseInt(roomsMatch[1], 10) : 1
        };

    }


    function validate(destination, checkin, checkout) {

        if (!destination) {
            return "Please enter a destination.";
        }

        if (!checkin) {
            return "Please select a check-in date.";
        }

        if (!checkout) {
            return "Please select a check-out date.";
        }

        if (checkout <= checkin) {
            return "Check-out date must be after check-in date.";
        }

        return "";

    }


    function bindSubmit() {

        document.addEventListener(
            "click",
            function (event) {

                var button = event.target.closest("#hotel-search-submit");

                if (!button) {
                    return;
                }

                event.preventDefault();
                event.stopPropagation();

                var destInput = $("#hotel-dest");
                var checkinInput = $("#hotel-checkin");
                var checkoutInput = $("#hotel-checkout");
                var guestsSelect = $("#hotel-guests");

                var destination = destInput ? destInput.value.trim() : "";
                var checkin = checkinInput ? (checkinInput.dataset.isoDate || checkinInput.value) : "";
                var checkout = checkoutInput ? (checkoutInput.dataset.isoDate || checkoutInput.value) : "";

                var guestsRoomsText =
                    guestsSelect && guestsSelect.selectedIndex >= 0
                        ? guestsSelect.options[guestsSelect.selectedIndex].text
                        : "2 Guests, 1 Room";

                var error = validate(destination, checkin, checkout);

                if (error) {
                    alert(error);
                    return;
                }

                var parsed = parseGuestsAndRooms(guestsRoomsText);

                var params = new URLSearchParams();
                params.set("destination", destination);
                params.set("checkin", checkin);
                params.set("checkout", checkout);
                params.set("guests", String(parsed.guests));
                params.set("rooms", String(parsed.rooms));

                window.location.href = "/hotel/search/?" + params.toString();

            },
            true
        );

    }


    function initialize() {
        bindDestinationAutocomplete();
        bindDateRangePicker();
        bindSubmit();
    }


    if (document.readyState === "loading") {

        document.addEventListener(
            "DOMContentLoaded",
            initialize,
            { once: true }
        );

    } else {

        initialize();

    }


})();
