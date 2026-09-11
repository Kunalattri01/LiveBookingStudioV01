import json

from django.shortcuts import redirect, render
from django.views import View


class HotelConfirmationView(View):
    """Poll and display booking status after Book has been called."""

    def get(self, request):
        book_result = request.session.get("hotel_book_result") or {}
        if not book_result.get("booking_id"):
            return redirect("HotelPage")

        return render(
            request,
            "hotel/hotel_confirmation.html",
            {"book_result_json": json.dumps(book_result)},
        )
