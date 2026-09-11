(function () {
    "use strict";

    const review = window.__FLIGHT_REVIEW__ || {};
    const search = window.__FLIGHT_SEARCH_REQUEST__ || {};
    const travellerData = window.__FLIGHT_TRAVELLERS__ || {};
    const selectedSeats = Array.isArray(window.__FLIGHT_SELECTED_SEATS__) ? window.__FLIGHT_SELECTED_SEATS__ : [];

    const routeEl = document.getElementById("review-route");
    const totalFareEl = document.getElementById("review-total-fare");
    const travellerListEl = document.getElementById("review-traveller-list");
    const seatListEl = document.getElementById("review-seat-list");

    function money(value) {
        const amount = Number(value);
        if (!Number.isFinite(amount)) return "\u20b9 0";
        return "\u20b9 " + amount.toLocaleString("en-IN", { maximumFractionDigits: 2 });
    }

    function escapeHtml(value) {
        return String(value == null ? "" : value).replace(/[&<>"']/g, function (char) {
            return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char];
        });
    }

    if (routeEl) {
        const origin = search.origin || (search.segments && search.segments[0] && search.segments[0].origin) || "";
        const destination = search.destination || (search.segments && search.segments[0] && search.segments[0].destination) || "";
        routeEl.textContent = origin && destination ? origin + " \u2192 " + destination : "Route not available";
    }

    if (totalFareEl) {
        totalFareEl.textContent = money(review.total_fare);
    }

    if (travellerListEl) {
        const travellers = Array.isArray(travellerData.travellers) ? travellerData.travellers : [];
        if (!travellers.length) {
            travellerListEl.textContent = "No traveller details found.";
        } else {
            travellerListEl.innerHTML = travellers.map(function (traveller, index) {
                const name = [traveller.fN, traveller.lN].filter(Boolean).join(" ") || "Traveller " + (index + 1);
                return "<div>" + escapeHtml(name) + " &middot; " + escapeHtml(traveller.pt || "ADULT") + "</div>";
            }).join("");
        }
    }

    if (seatListEl) {
        if (!selectedSeats.length) {
            seatListEl.textContent = "No seats were selected for this booking.";
        } else {
            seatListEl.innerHTML = selectedSeats.map(function (seat) {
                return "<div>Traveller " + (Number(seat.passenger_index) + 1) + ": seat " + escapeHtml(seat.code) + "</div>";
            }).join("");
        }
    }
})();
