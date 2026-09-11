/* ================================================================
   HOTEL BOOKING (TRAVELLER DETAILS) PAGE
   Renders the reviewed option from the session (embedded server-
   side) and posts guest/delivery details to /api/v1/hotels/book/.
   ================================================================ */
(function () {
    "use strict";

    const review = window.__HOTEL_REVIEW__;

    function $(selector, root) { return (root || document).querySelector(selector); }
    function show(el) { if (el) el.classList.remove("hidden"); }
    function hide(el) { if (el) el.classList.add("hidden"); }

    function formatPrice(value, currency) {
        if (typeof value !== "number") return "—";
        return (currency || "₹") + " " + value.toLocaleString("en-IN");
    }

    function getCsrfToken() {
        const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : "";
    }

    function renderSummary() {
        if (!review || !review.option) return;
        const option = review.option;
        const pricing = option.pricing || {};

        $("#hotel-booking-subtitle").textContent =
            (review.hotel_name || "") + " · " + (option.meal_basis || "") ;
        $("#hotel-booking-hotel-name").textContent = review.hotel_name || "";
        $("#hotel-booking-room-name").textContent =
            (option.room_info || []).map(function (r) { return r.name; }).filter(Boolean).join(" + ");
        $("#hotel-booking-base").textContent = formatPrice(pricing.base_price, pricing.currency);
        $("#hotel-booking-taxes").textContent = formatPrice((pricing.taxes || 0) + (pricing.mf || 0) + (pricing.mft || 0), pricing.currency);
        $("#hotel-booking-total").textContent = formatPrice(pricing.total_price, pricing.currency);
    }

    function renderTravellerForms() {
        const container = $("#hotel-booking-travellers");
        container.innerHTML = "";
        const rooms = (review && review.option && review.option.room_info) || [{ name: "Room 1" }];
        const compliance = (review && review.option && review.option.compliance) || {};
        const template = $("#hotel-traveller-template");

        rooms.forEach(function (room, index) {
            const block = template.content.cloneNode(true);
            block.querySelector(".js-room-label").textContent = "Room " + (index + 1) + (room.name ? " · " + room.name : "");

            const panField = block.querySelector(".js-pan");
            if (compliance.pan_required) {
                panField.classList.remove("hidden");
                panField.required = true;
            }

            const passportField = block.querySelector(".js-passport");
            if (compliance.passport_required) {
                passportField.classList.remove("hidden");
                passportField.required = true;
            }

            container.appendChild(block);
        });
    }

    function collectRoomTravellerInfo() {
        const rows = document.querySelectorAll("#hotel-booking-travellers > div");
        return Array.from(rows).map(function (row) {
            const traveller = {
                title: row.querySelector(".js-title").value,
                passenger_type: "ADULT",
                first_name: row.querySelector(".js-first-name").value.trim(),
                last_name: row.querySelector(".js-last-name").value.trim()
            };

            const panField = row.querySelector(".js-pan");
            if (panField && !panField.classList.contains("hidden") && panField.value.trim()) {
                traveller.pan = panField.value.trim();
            }

            const passportField = row.querySelector(".js-passport");
            if (passportField && !passportField.classList.contains("hidden") && passportField.value.trim()) {
                traveller.passport_number = passportField.value.trim();
            }

            return { travellers: [traveller] };
        });
    }

    function showError(message) {
        $("#hotel-booking-error-message").textContent = message;
        show($("#hotel-booking-error"));
    }

    function bindSubmit() {
        const form = $("#hotel-booking-form");
        const button = $("#hotel-booking-submit");

        form.addEventListener("submit", function (event) {
            event.preventDefault();
            hide($("#hotel-booking-error"));

            if (!review || !review.booking_id) {
                showError("Your reviewed selection has expired. Please search again.");
                return;
            }

            const payload = {
                booking_id: review.booking_id,
                room_traveller_info: collectRoomTravellerInfo(),
                delivery_info: {
                    emails: [$("#hotel-contact-email").value.trim()],
                    contacts: [$("#hotel-contact-phone").value.trim()],
                    codes: [$("#hotel-contact-code").value.trim()]
                },
                amount: review.option && review.option.pricing ? review.option.pricing.total_price : undefined
            };

            button.disabled = true;
            button.textContent = "Processing…";

            fetch("/api/v1/hotels/book/", {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": getCsrfToken() },
                body: JSON.stringify(payload)
            })
                .then(function (response) {
                    return response.json().then(function (data) { return { status: response.status, data: data }; });
                })
                .then(function (result) {
                    if (result.status === 200 && result.data.success) {
                        window.location.href = "/hotel/hotel-confirmation/";
                        return;
                    }
                    throw new Error(result.data.error_message || "Could not complete your booking.");
                })
                .catch(function (error) {
                    button.disabled = false;
                    button.textContent = "PAY & BOOK";
                    showError(error.message);
                });
        });
    }

    function initialize() {
        renderSummary();
        renderTravellerForms();
        bindSubmit();
    }

    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize, { once: true });
    else initialize();
})();
