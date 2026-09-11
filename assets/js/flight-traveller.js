(function () {
    "use strict";

    const review = window.__FLIGHT_REVIEW__ || {};
    const search = window.__FLIGHT_SEARCH_REQUEST__ || {};
    const isInternational = window.__FLIGHT_IS_INTERNATIONAL__ === true;
    const list = document.getElementById("traveller-list");
    const form = document.getElementById("traveller-form");
    const error = document.getElementById("traveller-error");

    // TripJack's own review response is the source of truth when it
    // actually tells us - but in practice it usually doesn't, so for
    // international trips we still ask (just not as a hard block),
    // and for plain domestic trips with no explicit requirement we
    // don't show the passport fields at all.
    const passportRequired = review.passport_required === true;
    const showPassportFields = passportRequired || isInternational;

    function csrf() {
        const match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : "";
    }

    function field(label, name, required, type, autocomplete) {
        return '<label>' + label + '<input ' + (required ? "required " : "") +
            'name="' + name + '" type="' + (type || "text") + '"' +
            (autocomplete ? ' autocomplete="' + autocomplete + '"' : "") +
            ' /></label>';
    }

    const adults = Number(search.adults || 1);
    const children = Number(search.children || 0);
    const infants = Number(search.infants || 0);
    const passengers = [];

    for (let i = 0; i < adults; i += 1) passengers.push({type: "ADULT", label: "Adult"});
    for (let i = 0; i < children; i += 1) passengers.push({type: "CHILD", label: "Child"});
    for (let i = 0; i < infants; i += 1) passengers.push({type: "INFANT", label: "Infant"});

    function renderPassenger(passenger, index) {
        const section = document.createElement("section");
        section.className = "traveller-card";
        section.dataset.passengerType = passenger.type;
        section.innerHTML =
            '<div class="traveller-card-title">' +
                '<div class="traveller-card-icon"><i class="fa-solid fa-user"></i></div>' +
                '<div class="traveller-card-heading"><p class="traveller-eyebrow">PASSENGER ' + (index + 1) + '</p>' +
                '<h2>' + passenger.label + ' ' + (index + 1) + '</h2>' +
                '<p>Enter the name exactly as shown on the travel document.</p></div>' +
                '<span class="traveller-type">' + passenger.type + '</span>' +
            '</div>' +
            '<div class="traveller-fields traveller-name-fields">' +
                field("Title", "traveller_" + index + "_title", true) +
                field("First name", "traveller_" + index + "_first_name", true, "text", "given-name") +
                field("Last name", "traveller_" + index + "_last_name", true, "text", "family-name") +
            '</div>' +
            '<div class="traveller-fields traveller-extra-fields">' +
                (passenger.type !== "ADULT" ? field("Date of birth", "traveller_" + index + "_dob", true, "date", "bday") : "") +
                '<div class="traveller-field-hint"><i class="fa-solid fa-circle-info"></i><span>Age-specific details are used only when required by the selected fare or airline.</span></div>' +
            '</div>' +
            (showPassportFields ?
            '<div class="traveller-document-fields ' + (passportRequired ? "" : "is-optional") + '">' +
                '<div class="document-heading"><strong>Travel document</strong><span>' +
                    (passportRequired ? "Required for this itinerary" : "Recommended for international travel") +
                '</span></div>' +
                '<div class="traveller-fields">' +
                    field("Nationality", "traveller_" + index + "_nationality", passportRequired) +
                    field("Passport number", "traveller_" + index + "_passport_number", passportRequired) +
                    field("Passport expiry", "traveller_" + index + "_passport_expiry", passportRequired, "date") +
                '</div>' +
            '</div>' : "");
        return section;
    }

    passengers.forEach(function (passenger, index) {
        list.appendChild(renderPassenger(passenger, index));
    });

    const summary = document.getElementById("traveller-trip-summary");
    if (summary) {
        const segments = Array.isArray(search.segments) ? search.segments : [];
        const route = segments.length
            ? segments.map(function (segment) { return segment.origin + " → " + segment.destination; }).join("  ·  ")
            : ((search.origin || "—") + " → " + (search.destination || "—"));
        const count = passengers.length;
        summary.innerHTML =
            '<div class="summary-route">' + route + '</div>' +
            '<div class="summary-passengers"><i class="fa-solid fa-users"></i><span>' + count +
            ' passenger' + (count === 1 ? "" : "s") + '</span></div>';
    }

    const passengerCount = document.getElementById("passenger-count");
    if (passengerCount) passengerCount.textContent = passengers.length;

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        error.classList.add("hidden");

        const formData = new FormData(form);
        const travellers = passengers.map(function (passenger, index) {
            return {
                ti: formData.get("traveller_" + index + "_title"),
                fN: formData.get("traveller_" + index + "_first_name"),
                lN: formData.get("traveller_" + index + "_last_name"),
                pt: passenger.type,
                dob: formData.get("traveller_" + index + "_dob") || undefined,
                pNat: formData.get("traveller_" + index + "_nationality") || undefined,
                pNum: formData.get("traveller_" + index + "_passport_number") || undefined,
                eD: formData.get("traveller_" + index + "_passport_expiry") || undefined
            };
        });

        const submit = form.querySelector("button[type=submit]");
        submit.disabled = true;
        submit.classList.add("is-loading");

        fetch("/api/v1/flights/traveller/", {
            method: "POST",
            headers: {"Content-Type": "application/json", "X-CSRFToken": csrf()},
            body: JSON.stringify({travellers: travellers, email: formData.get("email"), mobile: formData.get("mobile")})
        })
            .then(function (response) {
                return response.json().then(function (data) { return {status: response.status, data: data}; });
            })
            .then(function (result) {
                if (result.status !== 200 || !result.data.success) {
                    throw new Error(result.data.error_message || "Traveller details could not be saved.");
                }
                window.location.href = result.data.redirect_url || "/flight/seat-selection/";
            })
            .catch(function (requestError) {
                error.textContent = requestError.message || "Traveller details could not be saved.";
                error.classList.remove("hidden");
                submit.disabled = false;
                submit.classList.remove("is-loading");
            });
    });
})();
