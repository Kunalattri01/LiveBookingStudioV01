import json

from django.shortcuts import redirect, render
from django.views import View


class BookingReviewView(View):
    """
    Shows everything the traveller has put together so far - route,
    fare, travellers, seats if any were picked - in one place before
    the payment step (which isn't built yet). This is the page that
    comes right after seat selection.

    If someone lands here without finishing the earlier steps, we
    just send them back to where they need to pick up, rather than
    showing a half-empty page.
    """

    def get(self, request):
        review = request.session.get("flight_review") or {}
        if not review.get("booking_id"):
            return redirect("FlightFarePage")

        travellers = request.session.get("flight_travellers") or {}
        if not travellers.get("travellers"):
            return redirect("TravellerPage")

        search = request.session.get("flight_search_request") or {}
        seat_map = request.session.get("flight_seat_map") or {}
        selected_seats = request.session.get("selected_seats") or []

        return render(
            request,
            "flight/booking_review.html",
            {
                "review_json": json.dumps(review),
                "search_request_json": json.dumps(search),
                "travellers_json": json.dumps(travellers),
                "seat_map_json": json.dumps(seat_map),
                "selected_seats_json": json.dumps(selected_seats),
            },
        )
