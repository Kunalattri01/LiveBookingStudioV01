from django.shortcuts import redirect, render
from django.views import View

import json

class FlightFareView(View):
    """Render the fare-selection step for the server-side flight selection."""

    def get(self, request):
        selected = request.session.get("flight_selection") or []

        if not selected:
            return redirect("FlightResultsPage")

        return render(request, "flight/flight_fare.html", 
            {
                "selected_flights_json": json.dumps(selected)
            }
        )
