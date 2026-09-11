from dataclasses import asdict

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Hotel
from ..services.dto import HotelDetailResult, HotelSearchResult
from ..services.hotel_service import HotelService
from ..services.validators import validate_detail_payload, validate_search_payload
from .serializers import HotelDestinationCitySerializer, HotelDestinationHotelSerializer

_STATUS_CODE_BY_ERROR = {
    "hotel_provider_not_configured": status.HTTP_503_SERVICE_UNAVAILABLE,
    "provider_request_not_supported": status.HTTP_501_NOT_IMPLEMENTED,
    "hotel_provider_error": status.HTTP_502_BAD_GATEWAY,
}


def _error_response(error_code, error_message):
    http_status = _STATUS_CODE_BY_ERROR.get(error_code, status.HTTP_503_SERVICE_UNAVAILABLE)
    return Response(
        {"success": False, "error_code": error_code, "error_message": error_message},
        status=http_status,
    )


class HotelDestinationSearchApiView(APIView):
    """
    GET /api/v1/hotels/destinations/?q=...

    Autocomplete over the local Hotel master table (hotel/models.py),
    the same table hotel.services.validators resolves a typed
    destination into TripJack `hids` with. Returns two separate,
    typed lists rather than one flat one, so the frontend can render
    "cities" and "hotels" as distinct suggestion groups:

        cities: distinct city names matching the query (or, for an
                empty query, our most-popular cities) with a real
                hotel_count from the catalog - never a fabricated number.
        hotels: individual hotel name matches, each carrying its city
                so the UI can show "Hotel in {city}".
    """

    def get(self, request):
        query = (request.query_params.get("q") or "").strip()
        active_hotels = Hotel.objects.filter(is_active=True)

        city_qs = active_hotels
        if query:
            city_qs = city_qs.filter(city__icontains=query)

        city_rows = (
            city_qs.values("city", "country")
            .distinct()
            .order_by("city")[:20]
        )
        # Rank by how many hotels we actually have in that city (a real
        # count, not popularity metadata) so bigger, more useful
        # destinations surface first.
        cities = []
        for row in city_rows:
            count = active_hotels.filter(city=row["city"]).count()
            cities.append({"city": row["city"], "country": row["country"], "hotel_count": count})
        cities.sort(key=lambda c: -c["hotel_count"])
        cities = cities[:6]

        hotels = []
        if query:
            hotel_qs = active_hotels.filter(name__icontains=query).order_by("-is_popular", "name")[:8]
            hotels = [{"tj_hotel_id": h.tj_hotel_id, "name": h.name, "city": h.city} for h in hotel_qs]

        city_serializer = HotelDestinationCitySerializer(cities, many=True)
        hotel_serializer = HotelDestinationHotelSerializer(hotels, many=True)

        return Response(
            {"cities": city_serializer.data, "hotels": hotel_serializer.data},
            status=status.HTTP_200_OK,
        )


class HotelListingApiView(APIView):
    """
    POST /api/v1/hotels/listing/

    Step 1 of the booking flow. Real hotel-search entry point for
    web/mobile clients:

        Web/Mobile -> this view -> HotelService -> SupplierManager
            -> UnconfiguredHotelProvider (until HOTEL_PROVIDER is configured)
            -> controlled HTTP 503

    Never returns synthetic/mock data. Never persists the search or
    its results.
    """

    def post(self, request):
        search_request, errors = validate_search_payload(dict(request.data))

        if errors:
            return Response(
                {
                    "success": False,
                    "error_code": "invalid_search_request",
                    "error_message": " ".join(errors),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        result: HotelSearchResult = HotelService().search(search_request)

        if not result.success:
            return _error_response(result.error_code, result.error_message)

        return Response(
            {
                "success": True,
                "hotels": [asdict(h) for h in result.hotels],
                "correlation_id": result.correlation_id,
                "currency": result.currency,
                "nationality": result.nationality,
                "total_results": result.total_results,
            },
            status=status.HTTP_200_OK,
        )


class HotelPricingApiView(APIView):
    """
    POST /api/v1/hotels/pricing/

    Step 2 of the booking flow (Dynamic Detail). Returns every
    bookable option for a single hotel, including the reviewHash
    required by the Review step.
    """

    def post(self, request):
        detail_request, errors = validate_detail_payload(dict(request.data))

        if errors:
            return Response(
                {
                    "success": False,
                    "error_code": "invalid_detail_request",
                    "error_message": " ".join(errors),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        result: HotelDetailResult = HotelService().detail(detail_request)

        if not result.success:
            return _error_response(result.error_code, result.error_message)

        return Response({"success": True, "detail": asdict(result.detail)}, status=status.HTTP_200_OK)
