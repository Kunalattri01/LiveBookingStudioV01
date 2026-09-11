/* ================================================================
   HOTEL LISTING PAGE
   Calls our own /api/v1/hotels/listing/ API only - never talks to
   TripJack directly, and only ever renders our normalized JSON.
   Every filter/count here is computed client-side from that response
   - nothing is fabricated (no fake ratings, review counts, or promos).
   ================================================================ */
(function () {
    "use strict";

    const searchRequest = window.__HOTEL_SEARCH_REQUEST__;
    let allHotels = [];
    let currentCorrelationId = null;
    let currentCurrency = null;
    let currentNationality = null;

    const PRICE_BUCKETS = [
        { key: "0-2000", min: 0, max: 2000 },
        { key: "2000-5000", min: 2000, max: 5000 },
        { key: "5000-10000", min: 5000, max: 10000 },
        { key: "10000-20000", min: 10000, max: 20000 },
        { key: "20000-Infinity", min: 20000, max: Infinity }
    ];

    const filterState = { nameQuery: "", priceBuckets: new Set(), stars: new Set(), freeCancellationOnly: false, mealPlans: new Set(), sort: "recommended" };

    function $(selector, root) { return (root || document).querySelector(selector); }
    function $all(selector, root) { return Array.from((root || document).querySelectorAll(selector)); }
    function show(el) { if (el) el.classList.remove("hidden"); }
    function hide(el) { if (el) el.classList.add("hidden"); }

    function formatPrice(value, currency) {
        if (typeof value !== "number") return "Price on request";
        return (currency || "₹") + " " + value.toLocaleString("en-IN");
    }

    function cheapestOption(hotel) {
        return (hotel.options && hotel.options[0]) || null;
    }

    function escapeHtml(value) {
        return String(value ?? "").replace(/[&<>"']/g, function (c) {
            return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c];
        });
    }

    function runSearch() {
        if (!searchRequest) {
            showError("Your search could not be read. Please search again from the homepage.");
            return;
        }

        fetch("/api/v1/hotels/listing/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(searchRequest)
        })
            .then(function (response) {
                return response.json().then(function (data) { return { status: response.status, data: data }; });
            })
            .then(function (result) {
                hide($("#hotel-listing-loading"));
                if (result.status !== 200 || !result.data.success) {
                    showError(friendlyError(result.data.error_code, result.data.error_message));
                    return;
                }
                const hotels = result.data.hotels || [];
                if (!hotels.length) {
                    show($("#hotel-listing-empty"));
                    return;
                }
                allHotels = hotels;
                currentCorrelationId = result.data.correlation_id;
                currentCurrency = result.data.currency;
                currentNationality = result.data.nationality;
                show($("#hotel-listing-layout"));
                setupFilters(hotels);
                bindStaticEvents();
                applyFilters();
            })
            .catch(function () {
                hide($("#hotel-listing-loading"));
                showError("We couldn't reach the search service. Please check your connection and try again.");
            });
    }

    function friendlyError(code, message) {
        const friendly = {
            hotel_provider_not_configured: "Live hotel search isn't configured yet on this environment.",
            provider_request_not_supported: "This search isn't supported yet.",
            hotel_provider_error: "The hotel search provider didn't respond. Please try again in a moment."
        };
        return friendly[code] || message || "Something went wrong with your search.";
    }

    function showError(message) {
        $("#hotel-listing-error-message").textContent = message;
        show($("#hotel-listing-error"));
    }

    function priceOf(hotel) {
        const option = cheapestOption(hotel);
        return option && option.pricing ? option.pricing.total_price : null;
    }

    function bucketLabel(bucket) {
        const currency = currentCurrency || searchRequest.currency || "₹";
        if (bucket.max === Infinity) return currency + (bucket.min).toLocaleString("en-IN") + "+";
        if (bucket.min === 0) return "Under " + currency + bucket.max.toLocaleString("en-IN");
        return currency + bucket.min.toLocaleString("en-IN") + " - " + currency + bucket.max.toLocaleString("en-IN");
    }

    function setupFilters(hotels) {
        // Price buckets, only ones with at least one hotel
        const priceContainer = $("#hotel-filter-price-options");
        priceContainer.innerHTML = "";
        PRICE_BUCKETS.forEach(function (bucket) {
            const count = hotels.filter(function (h) {
                const price = priceOf(h);
                return typeof price === "number" && price >= bucket.min && price < bucket.max;
            }).length;
            if (!count) return;
            priceContainer.appendChild(buildFilterRow("js-price-filter", bucket.key, bucketLabel(bucket), count));
        });

        // Star ratings present in results, descending
        const starCounts = {};
        hotels.forEach(function (h) {
            if (typeof h.star_rating === "number" && h.star_rating > 0) {
                starCounts[h.star_rating] = (starCounts[h.star_rating] || 0) + 1;
            }
        });
        const starContainer = $("#hotel-filter-star-options");
        starContainer.innerHTML = "";
        Object.keys(starCounts).map(Number).sort(function (a, b) { return b - a; }).forEach(function (stars) {
            const row = buildFilterRow("js-star-filter", String(stars), "★".repeat(stars), starCounts[stars], true);
            starContainer.appendChild(row);
        });
        if (!Object.keys(starCounts).length) hide($("#hotel-filter-star-group"));
        else show($("#hotel-filter-star-group"));

        // Free cancellation
        const freeCancelCount = hotels.filter(function (h) {
            const o = cheapestOption(h);
            return o && o.cancellation && o.cancellation.is_refundable;
        }).length;
        const cancelContainer = $("#hotel-filter-cancellation-options");
        cancelContainer.innerHTML = "";
        if (freeCancelCount) {
            cancelContainer.appendChild(buildFilterRow("js-cancel-filter", "free", "Free cancellation", freeCancelCount));
        }

        // Meal plans present
        const mealCounts = {};
        hotels.forEach(function (h) {
            const o = cheapestOption(h);
            if (o && o.meal_basis) mealCounts[o.meal_basis] = (mealCounts[o.meal_basis] || 0) + 1;
        });
        const mealContainer = $("#hotel-filter-meal-options");
        mealContainer.innerHTML = "";
        Object.keys(mealCounts).sort().forEach(function (plan) {
            mealContainer.appendChild(buildFilterRow("js-meal-filter", plan, plan, mealCounts[plan]));
        });
    }

    function buildFilterRow(cssClass, value, label, count, isStars) {
        const row = document.createElement("label");
        row.className = "filter-row";
        row.innerHTML =
            '<span class="filter-row-left"><input type="checkbox" class="' + cssClass + '" value="' + escapeHtml(value) + '" />' +
            (isStars ? '<span class="stars">' + escapeHtml(label) + '</span>' : '<span>' + escapeHtml(label) + '</span>') +
            '</span><span class="count">(' + count + ')</span>';
        return row;
    }

    function bindStaticEvents() {
        $("#hotel-filter-name").addEventListener("input", function (e) {
            filterState.nameQuery = e.target.value.trim().toLowerCase();
            applyFilters();
        });

        $("#hotel-filters-clear").addEventListener("click", function () {
            filterState.nameQuery = "";
            filterState.priceBuckets.clear();
            filterState.stars.clear();
            filterState.freeCancellationOnly = false;
            filterState.mealPlans.clear();
            filterState.sort = "recommended";
            $("#hotel-filter-name").value = "";
            $all(".js-price-filter, .js-star-filter, .js-cancel-filter, .js-meal-filter").forEach(function (c) { c.checked = false; });
            $all(".sort-tab").forEach(function (t) { t.classList.toggle("is-active", t.dataset.sort === "recommended"); });
            applyFilters();
        });

        $all(".sort-tab").forEach(function (tab) {
            tab.addEventListener("click", function () {
                filterState.sort = tab.dataset.sort;
                $all(".sort-tab").forEach(function (t) { t.classList.toggle("is-active", t === tab); });
                applyFilters();
            });
        });

        // Delegated change handling since filter option lists are rebuilt per-search
        $("#hotel-filters").addEventListener("change", function (e) {
            const el = e.target;
            if (el.classList.contains("js-price-filter")) {
                toggleSetValue(filterState.priceBuckets, el.value, el.checked);
            } else if (el.classList.contains("js-star-filter")) {
                toggleSetValue(filterState.stars, Number(el.value), el.checked);
            } else if (el.classList.contains("js-cancel-filter")) {
                filterState.freeCancellationOnly = el.checked;
            } else if (el.classList.contains("js-meal-filter")) {
                toggleSetValue(filterState.mealPlans, el.value, el.checked);
            } else {
                return;
            }
            applyFilters();
        });
    }

    function toggleSetValue(set, value, checked) {
        if (checked) set.add(value);
        else set.delete(value);
    }

    function matchesPriceBuckets(hotel) {
        if (!filterState.priceBuckets.size) return true;
        const price = priceOf(hotel);
        if (typeof price !== "number") return false;
        return PRICE_BUCKETS.some(function (bucket) {
            return filterState.priceBuckets.has(bucket.key) && price >= bucket.min && price < bucket.max;
        });
    }

    function applyFilters() {
        let filtered = allHotels.filter(function (hotel) {
            const option = cheapestOption(hotel);
            if (!option) return false;

            if (filterState.nameQuery && !(hotel.name || "").toLowerCase().includes(filterState.nameQuery)) return false;

            if (!matchesPriceBuckets(hotel)) return false;

            if (filterState.stars.size && !filterState.stars.has(hotel.star_rating)) return false;

            if (filterState.freeCancellationOnly && !(option.cancellation && option.cancellation.is_refundable)) return false;

            if (filterState.mealPlans.size > 0 && !filterState.mealPlans.has(option.meal_basis)) return false;

            return true;
        });

        if (filterState.sort === "price_asc" || filterState.sort === "price_desc") {
            filtered = filtered.slice().sort(function (a, b) {
                const pa = priceOf(a) || 0;
                const pb = priceOf(b) || 0;
                return filterState.sort === "price_asc" ? pa - pb : pb - pa;
            });
        }

        $("#hotel-listing-count").textContent = filtered.length;

        if (!filtered.length) {
            show($("#hotel-listing-nomatch"));
            $("#hotel-listing-results").innerHTML = "";
            return;
        }
        hide($("#hotel-listing-nomatch"));
        renderHotels(filtered);
    }

    function renderHotels(hotels) {
        const container = $("#hotel-listing-results");
        container.innerHTML = "";
        const template = $("#hotel-card-template");

        hotels.forEach(function (hotel) {
            const card = template.content.cloneNode(true);
            const option = cheapestOption(hotel);

            const nameEl = card.querySelector(".js-hotel-name");
            if (nameEl) nameEl.textContent = hotel.name || "Unnamed property";

            const starsEl = card.querySelector(".js-hotel-stars");
            if (starsEl) starsEl.textContent = hotel.star_rating ? "★".repeat(hotel.star_rating) : "";

            const locEl = card.querySelector(".js-hotel-loc");
            if (locEl) locEl.textContent = searchRequest.destination || "";

            const imgWrap = card.querySelector(".js-hotel-img-wrap");
            const imgEl = card.querySelector(".js-hotel-img");
            const placeholderEl = card.querySelector(".js-hotel-img-placeholder");
            if (hotel.image_url && imgEl) {
                imgEl.src = hotel.image_url;
                imgEl.alt = hotel.name || "";
                show(imgEl);
                if (placeholderEl) hide(placeholderEl);
                imgEl.addEventListener("error", function () {
                    hide(imgEl);
                    if (placeholderEl) show(placeholderEl);
                });
            }

            const highlightsEl = card.querySelector(".js-hotel-highlights");
            if (highlightsEl && option) {
                const lines = [];
                if (option.cancellation && option.cancellation.is_refundable) {
                    lines.push('<span><i class="fa-solid fa-check"></i> Free cancellation</span>');
                }
                if (option.meal_basis && option.meal_basis !== "Room Only") {
                    lines.push('<span><i class="fa-solid fa-utensils"></i> ' + escapeHtml(option.meal_basis) + ' included</span>');
                }
                if (option.compliance && option.compliance.pan_required) {
                    lines.push('<span><i class="fa-solid fa-id-card"></i> PAN required at booking</span>');
                }
                highlightsEl.innerHTML = lines.join("");
            }

            const priceEl = card.querySelector(".js-hotel-price");
            if (priceEl) {
                priceEl.textContent = option && option.pricing
                    ? formatPrice(option.pricing.total_price, option.pricing.currency || currentCurrency)
                    : "Price on request";
            }

            const link = card.querySelector(".js-hotel-view-rooms");
            if (link) {
                const params = new URLSearchParams();
                params.set("hid", hotel.tj_hotel_id || "");
                params.set("checkin", searchRequest.check_in);
                params.set("checkout", searchRequest.check_out);
                params.set("currency", currentCurrency || searchRequest.currency);
                params.set("nationality", currentNationality || searchRequest.nationality);
                params.set("correlation_id", currentCorrelationId);
                params.set("rooms_json", JSON.stringify(searchRequest.rooms));
                link.href = "/hotel/hotel-detail/?" + params.toString();
            }

            container.appendChild(card);
        });
    }

    function initialize() { runSearch(); }

    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize, { once: true });
    else initialize();
})();
