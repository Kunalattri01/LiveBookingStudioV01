import json

from django.shortcuts import redirect, render
from django.views import View

from ..models import Airport


class TravellerView(View):
    """Collect traveller information after the selected fare is reviewed."""

    def get(self, request):

        review = request.session.get("flight_review") or {}
        if not review.get("booking_id"):
            return redirect("FlightFarePage")

        search = request.session.get("flight_search_request") or {}

        return render(request, "flight/traveller.html",
            {
                "review_json": json.dumps(review),
                "search_request_json": json.dumps(search),
                "is_international_json": json.dumps(self._is_international_trip(search)),
            }
        )

    def _is_international_trip(self, search):
        """
        TripJack's booking flow doesn't reliably tell us whether
        passport details are required for a given itinerary - we
        checked, and none of the real captured review responses carry
        a passport-required flag (only the after-booking detail
        response ever mentions passport, and only as an echo of what
        was submitted). So for anything that's genuinely international,
        we fall back to ordinary travel sense using our own airport
        master data, rather than guessing at TripJack's internals.
        """
        codes = set()

        if search.get("origin"):
            codes.add(search["origin"])
        if search.get("destination"):
            codes.add(search["destination"])

        for segment in search.get("segments") or []:
            if segment.get("origin"):
                codes.add(segment["origin"])
            if segment.get("destination"):
                codes.add(segment["destination"])

        if not codes:
            return False

        return Airport.objects.filter(code__in=codes).exclude(country_code="IN").exists()
