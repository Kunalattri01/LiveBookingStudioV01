/* ================================================================
   HOTEL CONFIRMATION PAGE
   Polls /api/v1/hotels/booking-details/ every 5s (up to ~180s, per
   the TripJack Hotel API v3 reference) until a terminal status.
   ================================================================ */
(function () {
    "use strict";

    const bookResult = window.__HOTEL_BOOK_RESULT__;
    const POLL_INTERVAL_MS = 5000;
    const MAX_POLL_MS = 180000;
    const startedAt = Date.now();
    let pollTimer = null;

    function $(selector) { return document.querySelector(selector); }
    function show(el) { if (el) el.classList.remove("hidden"); }
    function hide(el) { if (el) el.classList.add("hidden"); }

    function formatPrice(value, currency) {
        if (typeof value !== "number") return "—";
        return (currency || "₹") + " " + value.toLocaleString("en-IN");
    }

    function isTerminalSuccess(status) {
        return typeof status === "string" && status.toUpperCase().indexOf("CONFIRM") !== -1;
    }

    function isTerminalFailure(status) {
        if (typeof status !== "string") return false;
        const upper = status.toUpperCase();
        return upper.indexOf("FAIL") !== -1 || upper.indexOf("CANCEL") !== -1;
    }

    function showSuccess(details) {
        hide($("#hotel-confirmation-pending"));
        $("#hotel-confirmation-id").textContent = details.confirmation_number || details.booking_id || "";
        $("#hotel-confirmation-name").textContent = details.hotel_name || "";
        $("#hotel-confirmation-total").textContent = formatPrice(details.amount, details.currency);
        show($("#hotel-confirmation-success"));
    }

    function showFailure(message) {
        hide($("#hotel-confirmation-pending"));
        $("#hotel-confirmation-failed-message").textContent = message;
        show($("#hotel-confirmation-failed"));
    }

    function poll() {
        if (!bookResult || !bookResult.booking_id) {
            showFailure("We couldn't find your booking reference. Please contact support with your payment details.");
            return;
        }

        fetch("/api/v1/hotels/booking-details/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ booking_id: bookResult.booking_id })
        })
            .then(function (response) {
                return response.json().then(function (data) { return { status: response.status, data: data }; });
            })
            .then(function (result) {
                if (result.status !== 200 || !result.data.success) {
                    scheduleNextPoll();
                    return;
                }

                const details = result.data.details;

                if (isTerminalSuccess(details.status)) {
                    showSuccess(details);
                    return;
                }

                if (isTerminalFailure(details.status)) {
                    showFailure("This booking could not be confirmed (status: " + details.status + "). Please contact support with booking ID " + (details.booking_id || bookResult.booking_id) + ".");
                    return;
                }

                scheduleNextPoll();
            })
            .catch(function () {
                scheduleNextPoll();
            });
    }

    function scheduleNextPoll() {
        if (Date.now() - startedAt >= MAX_POLL_MS) {
            showFailure(
                "This is taking longer than usual. Your booking (ID " + bookResult.booking_id +
                ") is still being confirmed by the property - please check back in a few minutes."
            );
            return;
        }
        pollTimer = window.setTimeout(poll, POLL_INTERVAL_MS);
    }

    function initialize() { poll(); }

    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize, { once: true });
    else initialize();
})();
