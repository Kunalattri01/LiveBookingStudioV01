import json
from urllib.parse import quote

from django.shortcuts import redirect, render
from django.views import View

from flight.models import Airport
from flight.services.validators import validate_search_payload


class FlightResultsView(View):
    """
    Receives and validates the homepage flight search submission, then
    renders the results page shell.

    The actual live search is performed client-side: this view embeds
    a validated, normalized search payload into the page as JSON, and
    templates/flight/flights.html's JavaScript (assets/js/flight-results.js)
    POSTs that payload to /api/v1/flights/search/ - the same endpoint
    used by any other client - and renders whatever our own API
    returns. This keeps FlightService/SupplierManager/TripJackAdapter
    as the single search entry point (no duplicate search logic here),
    gives a real loading state while TripJack responds, and ensures
    the frontend only ever sees our normalized JSON, never raw
    TripJack data.
    """

    def get(self, request):
        trip_type = request.GET.get("trip_type", "oneway")

        payload = {
            "trip_type": trip_type,
            "adults": request.GET.get("adults", "1"),
            "children": request.GET.get("children", "0"),
            "infants": request.GET.get("infants", "0"),
            "cabin_class": request.GET.get("cabin_class", "economy"),
            "special_fare": request.GET.get("special_fare", "regular"),
        }

        if trip_type == "multicity":
            raw_segments = request.GET.get("segments", "")
            try:
                payload["segments"] = json.loads(raw_segments) if raw_segments else []
            except (TypeError, ValueError):
                return redirect("/?search_error=" + quote("Invalid multi-city segment data."))
        else:
            payload["origin"] = request.GET.get("origin", "")
            payload["destination"] = request.GET.get("destination", "")
            payload["departure_date"] = request.GET.get("departure_date")
            payload["return_date"] = request.GET.get("return_date")

        search_request, errors = validate_search_payload(payload)

        if errors:
            return redirect("/?search_error=" + quote(" ".join(errors)))

        # Build the exact JSON body the client will POST to
        # /api/v1/flights/search/ - same shape the API already accepts.
        if search_request.trip_type == "multicity":
            api_payload = {
                "trip_type": search_request.trip_type,
                "segments": [
                    {
                        "origin": s.origin,
                        "destination": s.destination,
                        "departure_date": s.departure_date.isoformat(),
                    }
                    for s in search_request.segments
                ],
            }
        else:
            api_payload = {
                "trip_type": search_request.trip_type,
                "origin": search_request.origin,
                "destination": search_request.destination,
                "departure_date": search_request.departure_date.isoformat(),
            }
            if search_request.return_date:
                api_payload["return_date"] = search_request.return_date.isoformat()

        api_payload["adults"] = search_request.adults
        api_payload["children"] = search_request.children
        api_payload["infants"] = search_request.infants
        api_payload["cabin_class"] = search_request.cabin_class
        api_payload["special_fare"] = search_request.special_fare

        origin_airport = Airport.objects.filter(code=search_request.origin).first() if search_request.origin else None
        destination_airport = (
            Airport.objects.filter(code=search_request.destination).first()
            if search_request.destination
            else None
        )

        airport_seed = list(Airport.objects.filter(is_active=True).order_by("-is_popular", "city").values("code", "city", "airport_name"))

        context = {
            "trip_type": search_request.trip_type,
            "origin": origin_airport,
            "destination": destination_airport,
            "departure_date": search_request.departure_date,
            "return_date": search_request.return_date,
            "adults": search_request.adults,
            "children": search_request.children,
            "infants": search_request.infants,
            "cabin_class": search_request.cabin_class,
            "special_fare": search_request.special_fare,
            "segments": search_request.segments,
            "search_payload_json": json.dumps(api_payload),
            "frontend_page_size": getattr(__import__("django.conf", fromlist=["settings"]).settings, "FRONTEND_PAGE_SIZE", 20),
            "airport_seed_json": json.dumps([
                {"code": item["code"], "city": item["city"], "airport": item["airport_name"]}
                for item in airport_seed
            ]),
        }

        return render(request, "flight/flights.html", context)
