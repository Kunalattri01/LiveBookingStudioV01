/* ================================================================
   HOTEL DETAIL PAGE (room / rate selection)
   Calls /api/v1/hotels/pricing/ then /api/v1/hotels/review/ - our
   own API only, never TripJack directly.
   ================================================================ */
(function () {
    "use strict";

    const detailRequest = window.__HOTEL_DETAIL_REQUEST__;
    let reviewHash = null;
    let selecting = false;

    function $(selector, root) { return (root || document).querySelector(selector); }
    function show(el) { if (el) el.classList.remove("hidden"); }
    function hide(el) { if (el) el.classList.add("hidden"); }

    function formatPrice(value, currency) {
        if (typeof value !== "number") return "Price on request";
        return (currency || "₹") + " " + value.toLocaleString("en-IN");
    }

    function escapeHtml(value) {
        return String(value ?? "").replace(/[&<>"']/g, function (c) {
            return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c];
        });
    }

    function getCsrfToken() {
        const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : "";
    }

    function loadPricing() {
        if (!detailRequest) {
            showError("Your selection could not be read. Please search again from the homepage.");
            return;
        }

        fetch("/api/v1/hotels/pricing/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(detailRequest)
        })
            .then(function (response) {
                return response.json().then(function (data) { return { status: response.status, data: data }; });
            })
            .then(function (result) {
                hide($("#hotel-detail-loading"));
                if (result.status !== 200 || !result.data.success) {
                    showError(friendlyError(result.data.error_code, result.data.error_message));
                    return;
                }
                const detail = result.data.detail;
                reviewHash = detail.review_hash;
                $("#hotel-detail-name").textContent = detail.hotel_name || "Property";
                if (detail.star_rating) {
                    $("#hotel-detail-stars").textContent = "★".repeat(detail.star_rating);
                }
                if (detail.image_url) {
                    const img = $("#hotel-detail-img");
                    img.src = detail.image_url;
                    img.alt = detail.hotel_name || "";
                    show(img);
                }
                renderOptions(detail.options || []);
            })
            .catch(function () {
                hide($("#hotel-detail-loading"));
                showError("We couldn't reach the pricing service. Please try again.");
            });
    }

    function friendlyError(code, message) {
        const friendly = {
            hotel_provider_not_configured: "Live hotel pricing isn't configured yet on this environment.",
            hotel_provider_error: "The hotel provider didn't respond. Please try again in a moment."
        };
        return friendly[code] || message || "Something went wrong.";
    }

    function showError(message) {
        $("#hotel-detail-error-message").textContent = message;
        show($("#hotel-detail-error"));
    }

    function renderOptions(options) {
        const container = $("#hotel-detail-options");
        container.innerHTML = "";

        if (!options.length) {
            container.innerHTML = '<div class="card p-8 text-center"><p class="font-bold">No rooms currently available for these dates.</p></div>';
            return;
        }

        const template = $("#hotel-option-template");

        options.forEach(function (option) {
            const row = template.content.cloneNode(true);

            const roomNames = (option.room_info || []).map(function (r) { return r.name; }).filter(Boolean);
            row.querySelector(".js-option-room").textContent = roomNames.join(" + ") || "Room";
            row.querySelector(".js-option-meal").textContent = option.meal_basis || "";

            const tags = row.querySelector(".js-option-tags");
            if (option.cancellation && option.cancellation.is_refundable) {
                tags.innerHTML += '<span class="tag soft teal">Free Cancellation</span>';
            }
            if (option.compliance && option.compliance.pan_required) {
                tags.innerHTML += '<span class="tag bg-slate-100 muted">PAN required</span>';
            }
            if (option.compliance && option.compliance.passport_required) {
                tags.innerHTML += '<span class="tag bg-slate-100 muted">Passport required</span>';
            }

            const pricing = option.pricing || {};
            row.querySelector(".js-option-price").textContent = formatPrice(pricing.total_price, pricing.currency);
            row.querySelector(".js-option-price-breakup").textContent =
                "Base " + formatPrice(pricing.base_price, pricing.currency) +
                (pricing.taxes ? " + taxes " + formatPrice(pricing.taxes, pricing.currency) : "");

            const button = row.querySelector(".js-option-select");
            button.addEventListener("click", function () { selectOption(option, button); });

            container.appendChild(row);
        });
    }

    function selectOption(option, button) {
        if (selecting) return;
        selecting = true;
        button.disabled = true;
        button.textContent = "Confirming…";

        fetch("/api/v1/hotels/review/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": getCsrfToken() },
            body: JSON.stringify({
                correlation_id: detailRequest.correlation_id,
                option_id: option.option_id,
                review_hash: reviewHash,
                hid: detailRequest.hid
            })
        })
            .then(function (response) {
                return response.json().then(function (data) { return { status: response.status, data: data }; });
            })
            .then(function (result) {
                if (result.status === 200 && result.data.success) {
                    window.location.href = "/hotel/hotel-booking/";
                    return;
                }
                throw new Error(result.data.error_message || "This option is no longer available. Please choose another.");
            })
            .catch(function (error) {
                selecting = false;
                button.disabled = false;
                button.textContent = "Select & Continue";
                showError(error.message);
            });
    }

    function initialize() { loadPricing(); }

    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize, { once: true });
    else initialize();
})();
