(function () {
    "use strict";

    const review = window.__FLIGHT_REVIEW__ || {};
    const search = window.__FLIGHT_SEARCH_REQUEST__ || {};
    const travellerData = window.__FLIGHT_TRAVELLERS__ || {};
    const status = document.getElementById("seat-status");
    const grid = document.getElementById("seat-grid");
    const map = document.getElementById("seat-map");
    const errorBox = document.getElementById("seat-error");
    const aircraftName = document.getElementById("aircraft-name");
    const selectedList = document.getElementById("selected-seat-list");
    const selectedPrice = document.getElementById("selected-seat-price");
    const continueButton = document.getElementById("continue-seat");
    const fareInventory = document.getElementById("fare-inventory");
    const reviewTotal = document.getElementById("review-total");
    const passengerPicker = document.getElementById("seat-passenger-picker");

    const selectedSeats = new Map();
    const passengers = Array.isArray(travellerData.travellers) ? travellerData.travellers : [];
    const passengerCount = Math.max(1, passengers.length || Number(search.adults || 0) + Number(search.children || 0) + Number(search.infants || 0));
    let activePassenger = 0;

    // A fare with no seat map at all is normal - some suppliers just
    // don't offer seat selection for certain fares. When that
    // happens we still need to let the traveller move on, instead of
    // permanently blocking them on a step that has nothing to select.
    let seatMapAvailable = true;

    function csrf() {
        const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : "";
    }

    function escapeHtml(value) {
        return String(value == null ? "" : value).replace(/[&<>"']/g, function (char) {
            return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char];
        });
    }

    function money(value) {
        const amount = Number(value);
        if (!Number.isFinite(amount)) return "₹ 0";
        return "₹ " + amount.toLocaleString("en-IN", {maximumFractionDigits: 2});
    }

    function setError(message) {
        errorBox.textContent = message || "";
        errorBox.classList.toggle("hidden", !message);
    }

    function isUsableSeat(seat) {
        return seat && seat.available === true && seat.availability_known === true;
    }

    function passengerLabel(index) {
        const passenger = passengers[index] || {};
        const firstName = passenger.fN ? " " + passenger.fN : "";
        return (passenger.pt || "Passenger") + " " + (index + 1) + firstName;
    }

    function renderPassengerPicker() {
        if (!passengerPicker) return;
        passengerPicker.innerHTML = passengers.map(function (passenger, index) {
            const selected = selectedSeats.get(index);
            return '<button type="button" class="seat-passenger ' + (index === activePassenger ? "is-active" : "") + '" data-passenger="' + index + '">' +
                '<span class="seat-passenger-number">' + (index + 1) + '</span>' +
                '<span><strong>' + escapeHtml(passengerLabel(index)) + '</strong><small>' + (selected ? "Seat " + escapeHtml(selected.code) : "Choose a seat") + '</small></span>' +
            '</button>';
        }).join("");
        passengerPicker.querySelectorAll("[data-passenger]").forEach(function (button) {
            button.addEventListener("click", function () {
                activePassenger = Number(button.dataset.passenger);
                renderPassengerPicker();
                renderSelectionSummary();
            });
        });
    }

    function columnOrder(columns) {
        return columns.slice().sort(function (a, b) { return String(a).localeCompare(String(b), "en", {numeric: true}); });
    }

    function groupSeatsByRow(seats) {
        const rows = new Map();
        seats.forEach(function (seat) {
            if (seat.row == null || !seat.column) return;
            if (!rows.has(String(seat.row))) rows.set(String(seat.row), []);
            rows.get(String(seat.row)).push(seat);
        });
        return rows;
    }

    function renderSeatMap(seats) {
        grid.innerHTML = "";
        const rowMap = groupSeatsByRow(seats);
        const rows = Array.from(rowMap.keys()).sort(function (a, b) { return Number(a) - Number(b); });
        if (!rows.length) {
            status.textContent = "The supplier returned seats, but not enough row and column information to draw the aircraft layout.";
            return;
        }

        const columns = columnOrder(Array.from(new Set(seats.map(function (seat) { return seat.column; }))));
        const split = Math.ceil(columns.length / 2);
        const visualColumns = columns.slice(0, split).concat(["__AISLE__"], columns.slice(split));
        grid.style.setProperty("--seat-cols", visualColumns.length);

        const header = document.createElement("div");
        header.className = "seat-row seat-row-header";
        header.innerHTML = '<span></span>' + visualColumns.map(function (column) {
            return column === "__AISLE__" ? '<span class="aisle-label">AISLE</span>' : '<span class="column-label">' + escapeHtml(column) + '</span>';
        }).join("");
        grid.appendChild(header);

        rows.forEach(function (rowNumber) {
            const row = document.createElement("div");
            row.className = "seat-row";
            row.innerHTML = '<span class="row-label">' + escapeHtml(rowNumber) + '</span>';
            const byColumn = new Map(rowMap.get(rowNumber).map(function (seat) { return [String(seat.column), seat]; }));

            visualColumns.forEach(function (column) {
                if (column === "__AISLE__") {
                    const aisle = document.createElement("span");
                    aisle.className = "seat-aisle";
                    row.appendChild(aisle);
                    return;
                }
                const seat = byColumn.get(String(column));
                if (!seat) {
                    const empty = document.createElement("span");
                    empty.className = "seat-empty";
                    row.appendChild(empty);
                    return;
                }

                const button = document.createElement("button");
                button.type = "button";
                button.className = "seat";
                button.textContent = seat.code;
                button.title = buildSeatTitle(seat);
                button.setAttribute("aria-label", buildSeatTitle(seat));

                if (seat.exit_row) button.classList.add("exit");
                if (!isUsableSeat(seat)) {
                    button.disabled = true;
                    button.classList.add(seat.availability_known ? "unavailable" : "unknown");
                }

                let owner = null;
                selectedSeats.forEach(function (value, passengerIndex) {
                    if (value.code === seat.code) owner = passengerIndex;
                });
                if (owner !== null) {
                    button.classList.add("selected");
                    button.textContent = owner + 1;
                    button.title = passengerLabel(owner) + " · " + seat.code;
                }

                button.addEventListener("click", function () {
                    assignSeat(seat);
                    renderSeatMap(seats);
                    renderPassengerPicker();
                    renderSelectionSummary();
                });
                row.appendChild(button);
            });
            grid.appendChild(row);
        });
    }

    function buildSeatTitle(seat) {
        const parts = [seat.code];
        if (seat.seat_type) parts.push(seat.seat_type);
        if (seat.window === true) parts.push("Window");
        if (seat.aisle === true) parts.push("Aisle");
        if (seat.price != null) parts.push(money(seat.price));
        if (seat.exit_row) parts.push("Exit row");
        if (seat.available === false) parts.push("Unavailable");
        return parts.join(" · ");
    }

    function removeExistingSeatForPassenger(index) {
        selectedSeats.delete(index);
    }

    function findPassengerWithSeat(code) {
        let owner = null;
        selectedSeats.forEach(function (seat, index) { if (seat.code === code) owner = index; });
        return owner;
    }

    function assignSeat(seat) {
        if (!isUsableSeat(seat)) return;
        const existingOwner = findPassengerWithSeat(seat.code);
        if (existingOwner !== null) {
            if (existingOwner === activePassenger) {
                selectedSeats.delete(activePassenger);
            } else {
                setError(seat.code + " is already assigned to " + passengerLabel(existingOwner) + ".");
            }
            return;
        }
        removeExistingSeatForPassenger(activePassenger);
        selectedSeats.set(activePassenger, seat);
        setError("");
        if (activePassenger < passengerCount - 1) activePassenger += 1;
    }

    function renderSelectionSummary() {
        const seats = Array.from(selectedSeats.entries()).sort(function (a, b) { return a[0] - b[0]; });

        if (!seatMapAvailable) {
            selectedList.textContent = "No seat map available for this fare - you can continue without picking a seat.";
            selectedPrice.textContent = money(0);
            continueButton.disabled = false;
            continueButton.textContent = "Continue without seat selection";
            return;
        }

        if (!seats.length) selectedList.textContent = "No seats selected";
        else selectedList.innerHTML = seats.map(function (entry) {
            return '<span class="selected-seat-chip"><strong>' + (entry[0] + 1) + '</strong> ' + escapeHtml(passengerLabel(entry[0])) + ': ' + escapeHtml(entry[1].code) + '</span>';
        }).join("");

        const total = seats.reduce(function (sum, entry) { return sum + (Number(entry[1].price) || 0); }, 0);
        selectedPrice.textContent = money(total);
        continueButton.disabled = seats.length !== passengerCount;
        continueButton.textContent = seats.length === passengerCount ? "Continue" : "Select " + (passengerCount - seats.length) + " more";
    }

    function updateMetrics(seatMap) {
        const available = Number(seatMap.available_seats || 0);
        const unavailable = Number(seatMap.unavailable_seats || 0);
        status.textContent = seatMap.availability_known
            ? available + " seat" + (available === 1 ? "" : "s") + " available · " + unavailable + " unavailable"
            : "Only seats explicitly marked available by the supplier are selectable.";
        const fareSeats = Number(review.seats_available);
        fareInventory.textContent = Number.isFinite(fareSeats) && fareSeats > 0 ? fareSeats + " fare seats" : "Not provided";
        reviewTotal.textContent = money(review.total_fare);
        aircraftName.textContent = seatMap.aircraft || "Passenger cabin";
    }

    function loadSeatMap() {
        fetch("/api/v1/flights/seat-map/", {
            method: "POST",
            headers: {"Content-Type": "application/json", "X-CSRFToken": csrf()},
            body: JSON.stringify({booking_id: review.booking_id})
        })
            .then(function (response) { return response.json().then(function (data) { return {status: response.status, data: data}; }); })
            .then(function (result) {
                if (result.status !== 200 || !result.data.success) throw new Error(result.data.error_message || "Seat map could not be loaded.");
                const seatMap = result.data.seat_map || {};
                const seats = Array.isArray(seatMap.seats) ? seatMap.seats : [];
                updateMetrics(seatMap);
                if (!seats.length) {
                    seatMapAvailable = false;
                    status.textContent = "Seat selection is not available for this itinerary or fare. No seats were fabricated - you can continue without one.";
                    renderSelectionSummary();
                    return;
                }
                map.classList.remove("hidden");
                renderSeatMap(seats);
                renderPassengerPicker();
                renderSelectionSummary();
            })
            .catch(function (err) {
                setError(err.message);
                status.textContent = "We could not load the live seat map.";
            });
    }

    continueButton.addEventListener("click", function () {
        if (seatMapAvailable && selectedSeats.size !== passengerCount) {
            setError("Please select one seat for every traveller before continuing.");
            return;
        }
        const seats = seatMapAvailable
            ? Array.from(selectedSeats.entries()).sort(function (a, b) { return a[0] - b[0]; }).map(function (entry) {
                const passenger = passengers[entry[0]] || {};
                const seat = entry[1];
                return {passenger_index: entry[0], passenger_type: passenger.pt, code: seat.code, row: seat.row, column: seat.column, price: seat.price};
            })
            : [];
        continueButton.disabled = true;
        fetch("/api/v1/flights/seat-selection/", {
            method: "POST",
            headers: {"Content-Type": "application/json", "X-CSRFToken": csrf()},
            body: JSON.stringify({seats: seats})
        })
            .then(function (response) { return response.json().then(function (data) { return {status: response.status, data: data}; }); })
            .then(function (result) {
                if (result.status !== 200 || !result.data.success) throw new Error(result.data.error_message || "Could not save your seat selection.");
                status.textContent = "Saved. Taking you to the review page…";
                window.location.href = "/flight/review/";
            })
            .catch(function (err) { setError(err.message); })
            .finally(function () { renderSelectionSummary(); });
    });

    if (!review.booking_id) {
        setError("This booking review has expired. Please return to fare selection and review the fare again.");
        status.textContent = "Seat map unavailable.";
    } else if (!passengers.length) {
        setError("Traveller details are missing. Please return to the traveller page and complete passenger information.");
        continueButton.disabled = true;
    } else {
        loadSeatMap();
    }
})();
