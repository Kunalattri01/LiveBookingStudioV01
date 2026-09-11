import json
from urllib.parse import quote

from django.shortcuts import redirect, render
from django.views import View

from ..services.validators import validate_search_payload


class HotelListingView(View):
    """
    Renders the hotel results page shell.

    The actual live search is performed client-side: this view embeds
    a validated, normalized Listing payload into the page as JSON, and
    templates/hotel/hotel_listing.html's JavaScript
    (assets/js/hotel-listing.js) POSTs that payload to
    /api/v1/hotels/listing/ - the same endpoint used by any other
    client - and renders whatever our own API returns. The frontend
    never sees raw TripJack data.
    """

    def get(self, request):
        payload = {
            "destination": request.GET.get("destination", ""),
            "check_in": request.GET.get("checkin", ""),
            "check_out": request.GET.get("checkout", ""),
        }

        rooms_json = request.GET.get("rooms_json")
        if rooms_json:
            try:
                payload["rooms"] = json.loads(rooms_json)
            except (TypeError, ValueError):
                return redirect("/?search_error=" + quote("Invalid room configuration."))
        else:
            payload["guests"] = request.GET.get("guests", "2")
            payload["room_count"] = request.GET.get("rooms", "1")

        search_request, errors = validate_search_payload(payload)

        if errors:
            return redirect("/?search_error=" + quote(" ".join(errors)))

        api_payload = {
            "destination": search_request.destination,
            "hids": search_request.hids,
            "check_in": search_request.check_in.isoformat(),
            "check_out": search_request.check_out.isoformat(),
            "rooms": [
                {"adults": r.adults, "children": r.children, "child_ages": r.child_ages}
                for r in search_request.rooms
            ],
            "currency": search_request.currency,
            "nationality": search_request.nationality,
        }

        context = {
            "destination": search_request.destination,
            "check_in": search_request.check_in,
            "check_out": search_request.check_out,
            "search_payload_json": json.dumps(api_payload),
        }

        return render(request, "hotel/hotel_listing.html", context)
