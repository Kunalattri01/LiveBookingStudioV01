(function () {
    "use strict";

    const flights = window.__SELECTED_FLIGHTS__ || [];
    let selected = flights.map(function (flight) {
        return { flight: flight, fare: (flight.fares || [])[0] || null };
    });

    function $(selector) { return document.querySelector(selector); }
    function money(value, currency) { return typeof value === "number" ? (currency || "₹") + " " + value.toLocaleString("en-IN") : "Price on request"; }
    function escapeHtml(value) { return String(value == null ? "" : value).replace(/[&<>"']/g, function (c) { return ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"})[c]; }); }
    function csrf() { const m = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/); return m ? decodeURIComponent(m[1]) : ""; }

    function flightTitle(flight) {
        const first = (flight.segments || [])[0] || {};
        const last = (flight.segments || [])[flight.segments.length - 1] || first;
        return (first.origin || "") + " → " + (last.destination || "");
    }

    function render() {
        const container = $("#fare-options");
        const summary = $("#fare-summary");
        container.innerHTML = "";
        summary.innerHTML = "";

        selected.forEach(function (entry, flightIndex) {
            const flight = entry.flight;
            const fares = flight.fares || [];
            const block = document.createElement("section");
            block.className = "bg-white border border-slate-200 rounded-3xl p-5 shadow-sm";
            block.innerHTML = '<div class="flex items-center justify-between gap-4 mb-5"><div><p class="text-xs font-bold uppercase tracking-wider text-slate-400">' + escapeHtml(flight.leg_label || "Flight") + '</p><h2 class="text-lg font-black text-slate-900 mt-1">' + escapeHtml(flightTitle(flight)) + '</h2></div><span class="text-xs font-semibold text-slate-500">' + escapeHtml((flight.segments || []).length > 1 ? "Connecting" : "Non-stop") + '</span></div>';

            const list = document.createElement("div");
            list.className = "grid gap-3";
            fares.forEach(function (fare, fareIndex) {
                const option = document.createElement("button");
                option.type = "button";
                option.className = "w-full text-left border rounded-2xl p-4 transition " + (entry.fare === fare ? "border-primary bg-sky-50/60 ring-1 ring-primary" : "border-slate-200 hover:border-slate-300");
                const features = [fare.baggage && fare.baggage.checkin ? "Check-in " + fare.baggage.checkin : null, fare.baggage && fare.baggage.cabin ? "Cabin " + fare.baggage.cabin : null, fare.meal_included === true ? "Meal included" : null, typeof fare.seats_available === "number" ? fare.seats_available + " seats" : null].filter(Boolean);
                option.innerHTML = '<div class="flex items-start justify-between gap-4"><div><div class="flex items-center gap-2"><strong class="text-base text-slate-900">' + escapeHtml(fare.fare_type || fare.cabin_class || "Fare") + '</strong>' + (fare.booking_class ? '<span class="text-[10px] px-2 py-1 rounded-full bg-slate-100 text-slate-500">' + escapeHtml(fare.booking_class) + '</span>' : '') + '</div><p class="text-xs text-slate-500 mt-1">' + escapeHtml(features.join(" · ") || "Fare details provided by supplier") + '</p></div><strong class="text-lg text-slate-900">' + escapeHtml(money(fare.total_fare, fare.currency)) + '</strong></div>';
                option.addEventListener("click", function () { selected[flightIndex].fare = fare; render(); });
                list.appendChild(option);
            });
            block.appendChild(list);
            container.appendChild(block);

            const fare = entry.fare;
            const item = document.createElement("div");
            item.className = "flex justify-between gap-3 text-sm";
            item.innerHTML = '<span class="text-slate-500">' + escapeHtml(flightTitle(flight)) + '</span><strong>' + escapeHtml(fare ? money(fare.total_fare, fare.currency) : "—") + '</strong>';
            summary.appendChild(item);
        });

        $("#fare-review-button").disabled = selected.some(function (entry) { return !entry.fare || !entry.fare.fare_id; });
    }

    $("#fare-review-button").addEventListener("click", function () {
        const button = this;
        const error = $("#fare-error");
        error.classList.add("hidden");
        button.disabled = true;
        const priceIds = selected.map(function (entry) { return entry.fare.fare_id; });
        fetch("/api/v1/flights/review/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() },
            body: JSON.stringify({ price_ids: priceIds })
        }).then(function (response) {
            return response.json().then(function (data) { return { status: response.status, data: data }; });
        }).then(function (result) {
            if (result.status !== 200 || !result.data.success) throw new Error(result.data.error_message || "Fare review failed.");
            window.location.href = "/flight/traveller/";
        }).catch(function (err) {
            error.textContent = err.message;
            error.classList.remove("hidden");
            button.disabled = false;
        });
    });

    render();
})();
