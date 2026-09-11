from django.views import View
from django.http import JsonResponse
from django.db.models import Q

from flight.models import Airport


class AirportSearchView(View):
    """
        Backend-driven airport/city autocomplete for the homepage flight
        search widget. Reads only from our local Airport master data —
        never calls any flight supplier.
    """

    def get(self, request):
        query = (request.GET.get("q") or "").strip()

        airports = Airport.objects.filter(is_active=True)

        if query:
            airports = airports.filter(
                Q(code__icontains=query)
                | Q(city__icontains=query)
                | Q(airport_name__icontains=query)
            )

        airports = airports.order_by("-is_popular", "city")[:10]

        return JsonResponse({
            "results": [airport.to_dict() for airport in airports],
        })
