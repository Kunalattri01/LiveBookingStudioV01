import datetime

from django.test import SimpleTestCase

from flight.providers.tripjack_provider import TripJackAdapter
from flight.services.dto import FlightSegmentRequest, SearchRequest


class TripJackRequestMappingTests(SimpleTestCase):
    """
    Verifies our internal SearchRequest maps to EXACTLY the request
    shape confirmed working against TripJack UAT (captured via
    Postman). Only the one-way shape is verified/implemented.
    """

    def test_oneway_request_matches_verified_postman_shape(self):
        search_request = SearchRequest(
            trip_type="oneway",
            segments=[
                FlightSegmentRequest(
                    origin="DEL",
                    destination="GOI",
                    departure_date=datetime.date(2026, 9, 21),
                )
            ],
            adults=2,
            children=0,
            infants=0,
            cabin_class="economy",
        )

        payload = TripJackAdapter()._build_search_payload(search_request)

        self.assertEqual(
            payload,
            {
                "searchQuery": {
                    "cabinClass": "ECONOMY",
                    "paxInfo": {"ADULT": "2", "CHILD": "0", "INFANT": "0"},
                    "routeInfos": [
                        {
                            "fromCityOrAirport": {"code": "DEL"},
                            "toCityOrAirport": {"code": "GOI"},
                            "travelDate": "2026-09-21",
                        }
                    ],
                    "searchModifiers": {
                        "isDirectFlight": True,
                        "isConnectingFlight": True,
                    },
                }
            },
        )

    def test_pax_counts_are_strings_as_required_by_tripjack(self):
        search_request = SearchRequest(
            trip_type="oneway",
            segments=[
                FlightSegmentRequest(origin="DEL", destination="BOM", departure_date=datetime.date(2026, 10, 1))
            ],
            adults=1,
            children=2,
            infants=1,
        )

        payload = TripJackAdapter()._build_search_payload(search_request)
        pax_info = payload["searchQuery"]["paxInfo"]

        self.assertEqual(pax_info, {"ADULT": "1", "CHILD": "2", "INFANT": "1"})
        for value in pax_info.values():
            self.assertIsInstance(value, str)

    def test_cabin_class_uppercased(self):
        search_request = SearchRequest(
            trip_type="oneway",
            segments=[
                FlightSegmentRequest(origin="DEL", destination="BOM", departure_date=datetime.date(2026, 10, 1))
            ],
            cabin_class="premium_economy",
        )

        payload = TripJackAdapter()._build_search_payload(search_request)
        self.assertEqual(payload["searchQuery"]["cabinClass"], "PREMIUM_ECONOMY")

    def test_roundtrip_request_matches_official_collection_shape(self):
        """
        Per the official TripJack Flight/FMS Postman collection's
        "Air Search - Domestic Return" example: two routeInfos entries,
        outbound then return.
        """
        search_request = SearchRequest(
            trip_type="roundtrip",
            segments=[
                FlightSegmentRequest(origin="DEL", destination="BLR", departure_date=datetime.date(2026, 9, 4)),
                FlightSegmentRequest(origin="BLR", destination="DEL", departure_date=datetime.date(2026, 9, 10)),
            ],
            adults=1,
        )

        payload = TripJackAdapter()._build_search_payload(search_request)
        route_infos = payload["searchQuery"]["routeInfos"]

        self.assertEqual(len(route_infos), 2)
        self.assertEqual(route_infos[0], {
            "fromCityOrAirport": {"code": "DEL"},
            "toCityOrAirport": {"code": "BLR"},
            "travelDate": "2026-09-04",
        })
        self.assertEqual(route_infos[1], {
            "fromCityOrAirport": {"code": "BLR"},
            "toCityOrAirport": {"code": "DEL"},
            "travelDate": "2026-09-10",
        })

    def test_multicity_request_matches_official_collection_shape(self):
        """
        Per the official collection's "Air Search - Domestic Multicity"
        example: one routeInfos entry per leg, in order.
        """
        search_request = SearchRequest(
            trip_type="multicity",
            segments=[
                FlightSegmentRequest(origin="DEL", destination="BOM", departure_date=datetime.date(2026, 9, 4)),
                FlightSegmentRequest(origin="BOM", destination="BLR", departure_date=datetime.date(2026, 9, 8)),
                FlightSegmentRequest(origin="BLR", destination="DEL", departure_date=datetime.date(2026, 9, 12)),
            ],
            adults=1,
        )

        payload = TripJackAdapter()._build_search_payload(search_request)
        route_infos = payload["searchQuery"]["routeInfos"]

        self.assertEqual(len(route_infos), 3)
        self.assertEqual(
            [(r["fromCityOrAirport"]["code"], r["toCityOrAirport"]["code"]) for r in route_infos],
            [("DEL", "BOM"), ("BOM", "BLR"), ("BLR", "DEL")],
        )
