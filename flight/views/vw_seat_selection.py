import json

from django.shortcuts import redirect, render
from django.views import View


class SeatSelectionView(View):
    """Render seat selection after fare review."""

    def get(self, request):
        review = request.session.get("flight_review") or {}
        
        if not review.get("booking_id"):
            return redirect("FlightFarePage")
        return render(request, "flight/seat_selection.html", 
            {
                "review_json": json.dumps(review), 
                "search_request_json": json.dumps(request.session.get("flight_search_request") or {}), 
                "travellers_json": json.dumps(request.session.get("flight_travellers") or {})
            }
        )
