from urllib.parse import quote, urlencode

from django.shortcuts import redirect
from django.views import View


class HotelSearchView(View):
    """
    Receives the homepage hotel search submission (destination/checkin/
    checkout/guests/rooms querystring, built by assets/js/hotel-search.js)
    and forwards it to the listing page, which does the authoritative
    validation and renders live results.
    """

    def get(self, request):
        params = {
            "destination": request.GET.get("destination", ""),
            "checkin": request.GET.get("checkin", ""),
            "checkout": request.GET.get("checkout", ""),
            "guests": request.GET.get("guests", "2"),
            "rooms": request.GET.get("rooms", "1"),
        }

        if not params["destination"] or not params["checkin"] or not params["checkout"]:
            return redirect("/?search_error=" + quote("Please fill in destination, check-in and check-out."))

        return redirect("/hotel/hotel-listing/?" + urlencode(params))
