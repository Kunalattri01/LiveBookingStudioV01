from typing import List

from django.conf import settings

from ..normalizers.tripjack import TripJackNormalizer
from ..services.dto import SearchRequest, NormalizedFlight
from .base import FlightProvider
from .exceptions import ProviderUpstreamError


class TripJackAdapter(FlightProvider):
    """
    Adapter for TripJack flight inventory.

    REQUEST FORMAT: one-way, round-trip, and multi-city request
    building are all verified against the official TripJack "Flight/
    FMS" Postman collection, which confirms `routeInfos` accepts one
    entry per one-way search, two entries (outbound + return) for
    round-trip, and N entries for multi-city - all sent to the same
    `POST /fms/v1/air-search-all` endpoint. One-way was additionally
    confirmed with a real captured successful request/response.

    RESPONSE FORMAT: only the one-way response shape (`tripInfos.ONWARD`)
    has been verified against a real captured response. The official
    collection does not include sample response bodies for round-trip
    or multi-city, so exactly how TripJack structures a multi-leg
    response (key names beyond "ONWARD", how per-leg fares relate) is
    NOT verified. The normalizer handles this by iterating over
    whatever direction keys TripJack actually returns in `tripInfos`
    (see flight/normalizers/tripjack.py) rather than assuming specific
    key names like "RETURN" - this is a safe generalization of the
    verified structure, not a guess at new field semantics. Combining
    a chosen outbound + return fare into one bookable itinerary is a
    Review/Revalidate-step concern (per the official collection's "Air
    Review" examples, which pass multiple priceIds together) and is
    out of scope for this search-only phase.

    See docs/tripjack-integration.md for the full verification record
    and exactly what remains unverified.
    """

    SEARCH_PATH_NOTE = "/fms/v1/air-search-all"  # for reference only

    def __init__(self):
        self.api_key = getattr(settings, "TRIPJACK_API_KEY", "")
        self.base_url = getattr(settings, "TRIPJACK_BASE_URL", "")

    def search(self, search_request: SearchRequest) -> List[NormalizedFlight]:
        payload = self._build_search_payload(search_request)

        # Local import keeps TripJackClient's `requests` dependency out
        # of the import path for anything that never actually searches.
        from interactions.tripjack.client import TripJackClient
        from interactions.tripjack.exceptions import TripJackError

        client = TripJackClient()

        try:
            raw_response = client.search_flights(payload)
        except TripJackError as exc:
            raise ProviderUpstreamError(str(exc)) from exc

        normalizer = TripJackNormalizer()

        try:
            return normalizer.normalize(raw_response)
        except Exception as exc:  # noqa: BLE001 - normalization failure is an upstream-data problem
            raise ProviderUpstreamError(
                "TripJack returned a response that could not be normalized."
            ) from exc

    def _build_search_payload(self, search_request: SearchRequest) -> dict:
        """
        Builds the TripJack air-search-all request.

        One-way (1 routeInfos entry) is verified against a real
        successful captured request/response. Round-trip (2 entries)
        and multi-city (N entries) follow the exact `routeInfos` array
        pattern shown in the official TripJack Flight/FMS Postman
        collection ("Air Search - Domestic Return" and "Air Search -
        Domestic Multicity" examples), which the project owner
        supplied as the authoritative request-format reference:

            {
              "searchQuery": {
                "cabinClass": "ECONOMY",
                "paxInfo": {"ADULT": "2", "CHILD": "0", "INFANT": "0"},
                "routeInfos": [
                  {"fromCityOrAirport": {"code": "DEL"}, "toCityOrAirport": {"code": "GOI"}, "travelDate": "2026-09-21"},
                  ... one entry per segment ...
                ],
                "searchModifiers": {"isDirectFlight": true, "isConnectingFlight": false}
              }
            }

        NOTE: searchModifiers is fixed to direct-flights-only, matching
        our sole verified real request. The official collection's own
        examples use inconsistent isDirectFlight/isConnectingFlight
        combinations across its samples, so we deliberately keep using
        our known-working combination rather than guessing which of
        the collection's differing example values is "the" correct
        one. Exposing connecting-flight search as a user option is a
        known limitation (see docs/tripjack-integration.md).
        """

        route_infos = [
            {
                "fromCityOrAirport": {"code": segment.origin},
                "toCityOrAirport": {"code": segment.destination},
                "travelDate": segment.departure_date.isoformat(),
            }
            for segment in search_request.segments
        ]

        return {
            "searchQuery": {
                "cabinClass": search_request.cabin_class.upper(),
                "paxInfo": {
                    "ADULT": str(search_request.adults),
                    "CHILD": str(search_request.children),
                    "INFANT": str(search_request.infants),
                },
                "routeInfos": route_infos,
                "searchModifiers": {
                    "isDirectFlight": settings.TRIPJACK_INCLUDE_DIRECT_FLIGHTS,
                    "isConnectingFlight": settings.TRIPJACK_INCLUDE_CONNECTING_FLIGHTS,
                },
            }
        }
