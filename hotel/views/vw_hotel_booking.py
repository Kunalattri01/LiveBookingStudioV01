import json

from django.shortcuts import redirect, render
from django.views import View


class HotelBookingView(View):
    """Collect traveller/delivery information after the selected option is reviewed."""

    def get(self, request):
        review = request.session.get("hotel_review") or {}
        if not review.get("booking_id"):
            return redirect("HotelPage")

        return render(
            request,
            "hotel/hotel_booking.html",
            {"review_json": json.dumps(review)},
        )
