import json
from urllib.parse import quote

from django.shortcuts import redirect, render
from django.views import View

from ..services.validators import validate_detail_payload


class HotelDetailView(View):
    """
    Renders the hotel detail (room/rate selection) page shell.

    Reached from a listing card's "View Rooms" link, which carries the
    selected hid plus the same search parameters and the correlationId
    from the Listing response. As with the listing page, the live call
    (to /api/v1/hotels/pricing/) is made client-side by
    assets/js/hotel-detail.js.
    """

    def get(self, request):
        payload = {
            "hid": request.GET.get("hid", ""),
            "correlation_id": request.GET.get("correlation_id", ""),
            "check_in": request.GET.get("checkin", ""),
            "check_out": request.GET.get("checkout", ""),
            "currency": request.GET.get("currency", ""),
            "nationality": request.GET.get("nationality", ""),
        }

        rooms_json = request.GET.get("rooms_json")
        try:
            payload["rooms"] = json.loads(rooms_json) if rooms_json else []
        except (TypeError, ValueError):
            return redirect("/?search_error=" + quote("Invalid room configuration."))

        detail_request, errors = validate_detail_payload(payload)

        if errors:
            return redirect("/?search_error=" + quote(" ".join(errors)))

        api_payload = {
            "hid": detail_request.hid,
            "correlation_id": detail_request.correlation_id,
            "check_in": detail_request.check_in.isoformat(),
            "check_out": detail_request.check_out.isoformat(),
            "rooms": [
                {"adults": r.adults, "children": r.children, "child_ages": r.child_ages}
                for r in detail_request.rooms
            ],
            "currency": detail_request.currency,
            "nationality": detail_request.nationality,
        }

        context = {
            "hid": detail_request.hid,
            "check_in": detail_request.check_in,
            "check_out": detail_request.check_out,
            "detail_payload_json": json.dumps(api_payload),
        }

        return render(request, "hotel/hotel_detail.html", context)
