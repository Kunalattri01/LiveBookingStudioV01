from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Airport
from ..services.dto import SearchResult
from ..services.flight_service import FlightService
from ..services.validators import validate_search_payload
from .serializers import (
    AirportSerializer,
    FlightSearchRequestSerializer,
    NormalizedFlightSerializer,
)


class AirportSearchApiView(APIView):
    """
    GET /api/v1/airports/?q=...

    Versioned, documented equivalent of the existing homepage
    autocomplete endpoint (/flight/airports/). Both read the same
    Airport master data; kept separate so the existing homepage widget
    is not touched by this API's evolution.
    """

    def get(self, request):
        query = (request.query_params.get("q") or "").strip()

        airports = Airport.objects.filter(is_active=True)

        if query:
            airports = airports.filter(
                Q(code__icontains=query)
                | Q(city__icontains=query)
                | Q(airport_name__icontains=query)
            )

        airports = airports.order_by("-is_popular", "city")[:10]

        data = [
            {"code": a.code, "city": a.city, "airport": a.airport_name}
            for a in airports
        ]

        serializer = AirportSerializer(data, many=True)

        return Response({"results": serializer.data}, status=status.HTTP_200_OK)


class FlightSearchApiView(APIView):
    """
    POST /api/v1/flights/search/

    Real flight-search entry point for web/mobile clients:

        Web/Mobile -> this view -> FlightService -> SupplierManager
            -> UnconfiguredProvider (until TripJack is configured)
            -> controlled HTTP 503

    Never returns synthetic/mock data. Never persists the search or
    its results.
    """

    def post(self, request):
        shape_serializer = FlightSearchRequestSerializer(data=request.data)
        shape_serializer.is_valid(raise_exception=False)

        payload = dict(request.data)
        # DRF's QueryDict-style multi-value handling isn't needed here;
        # request.data for JSON requests is already a plain dict.

        search_request, errors = validate_search_payload(payload)

        if errors:
            return Response(
                {
                    "success": False,
                    "error_code": "invalid_search_request",
                    "error_message": " ".join(errors),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        result: SearchResult = FlightService().search(search_request)

        if not result.success:
            status_code_by_error = {
                "flight_provider_not_configured": status.HTTP_503_SERVICE_UNAVAILABLE,
                "provider_search_not_supported": status.HTTP_501_NOT_IMPLEMENTED,
                "flight_provider_error": status.HTTP_502_BAD_GATEWAY,
            }
            http_status = status_code_by_error.get(
                result.error_code, status.HTTP_503_SERVICE_UNAVAILABLE
            )

            return Response(
                {
                    "success": False,
                    "error_code": result.error_code,
                    "error_message": result.error_message,
                },
                status=http_status,
            )

        flights_data = NormalizedFlightSerializer(result.flights, many=True).data

        return Response(
            {"success": True, "flights": flights_data},
            status=status.HTTP_200_OK,
        )
