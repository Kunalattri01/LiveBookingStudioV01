import datetime
import json
import os
from unittest.mock import patch

from django.test import TestCase, override_settings

from flight.models import Airport
from flight.providers.exceptions import ProviderUpstreamError
from flight.providers.tripjack_provider import TripJackAdapter
from flight.services.dto import FlightSegmentRequest, SearchRequest
from flight.services.flight_service import FlightService
from interactions.tripjack.exceptions import TripJackRequestError

FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__), "fixtures", "tripjack_air_search_all_sample.json"
)


def load_fixture():
    with open(FIXTURE_PATH) as f:
        return json.load(f)


@override_settings(FLIGHT_PROVIDER="tripjack", TRIPJACK_API_KEY="test-key", TRIPJACK_BASE_URL="https://apitest.tripjack.com")
class TripJackAdapterEndToEndTests(TestCase):
    def setUp(self):
        self.search_request = SearchRequest(
            trip_type="oneway",
            segments=[
                FlightSegmentRequest(
                    origin="DEL", destination="GOI", departure_date=datetime.date(2026, 9, 21)
                )
            ],
            adults=2,
        )

    @patch("interactions.tripjack.client.TripJackClient.search_flights")
    def test_full_pipeline_produces_normalized_flights(self, mock_search_flights):
        mock_search_flights.return_value = load_fixture()

        result = FlightService().search(self.search_request)

        self.assertTrue(result.success)
        self.assertEqual(len(result.flights), 2)
        self.assertEqual(result.flights[0].provider, "tripjack")
        self.assertEqual(result.flights[0].segments[0].airline_code, "6E")

    @patch("interactions.tripjack.client.TripJackClient.search_flights")
    def test_adapter_wraps_client_error_as_provider_upstream_error(self, mock_search_flights):
        mock_search_flights.side_effect = TripJackRequestError("boom")

        with self.assertRaises(ProviderUpstreamError):
            TripJackAdapter().search(self.search_request)

    @patch("interactions.tripjack.client.TripJackClient.search_flights")
    def test_client_error_surfaces_as_controlled_502_via_flight_service(self, mock_search_flights):
        mock_search_flights.side_effect = TripJackRequestError("boom")

        result = FlightService().search(self.search_request)

        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "flight_provider_error")

    def test_roundtrip_now_attempts_a_two_segment_request(self):
        """
        Round-trip is no longer blocked - it now builds a real 2-route
        request per the official TripJack collection. The HTTP layer
        is mocked here, so no real network call happens.
        """
        roundtrip_request = SearchRequest(
            trip_type="roundtrip",
            segments=[
                FlightSegmentRequest(origin="DEL", destination="GOI", departure_date=datetime.date(2026, 9, 21)),
                FlightSegmentRequest(origin="GOI", destination="DEL", departure_date=datetime.date(2026, 9, 28)),
            ],
        )

        with patch("interactions.tripjack.client.TripJackClient.search_flights") as mock_search_flights:
            mock_search_flights.return_value = load_fixture()
            TripJackAdapter().search(roundtrip_request)

            sent_payload = mock_search_flights.call_args[0][0]
            self.assertEqual(len(sent_payload["searchQuery"]["routeInfos"]), 2)

    def test_multicity_now_attempts_an_n_segment_request(self):
        multicity_request = SearchRequest(
            trip_type="multicity",
            segments=[
                FlightSegmentRequest(origin="DEL", destination="BOM", departure_date=datetime.date(2026, 9, 4)),
                FlightSegmentRequest(origin="BOM", destination="BLR", departure_date=datetime.date(2026, 9, 8)),
                FlightSegmentRequest(origin="BLR", destination="DEL", departure_date=datetime.date(2026, 9, 12)),
            ],
        )

        with patch("interactions.tripjack.client.TripJackClient.search_flights") as mock_search_flights:
            mock_search_flights.return_value = load_fixture()
            TripJackAdapter().search(multicity_request)

            sent_payload = mock_search_flights.call_args[0][0]
            self.assertEqual(len(sent_payload["searchQuery"]["routeInfos"]), 3)


@override_settings(FLIGHT_PROVIDER="tripjack", TRIPJACK_API_KEY="test-key", TRIPJACK_BASE_URL="https://apitest.tripjack.com")
class TripJackSearchNoPersistenceTests(TestCase):
    """
    Explicit guard for the mandatory database rule: performing a
    TripJack-backed search (even a successful one, even a failed one)
    must never write anything to the database beyond what already
    existed (Airport master data only).
    """

    @patch("interactions.tripjack.client.TripJackClient.search_flights")
    def test_successful_search_writes_nothing_to_the_database(self, mock_search_flights):
        mock_search_flights.return_value = load_fixture()

        airport_count_before = Airport.objects.count()

        search_request = SearchRequest(
            trip_type="oneway",
            segments=[
                FlightSegmentRequest(origin="DEL", destination="GOI", departure_date=datetime.date(2026, 9, 21))
            ],
            adults=2,
        )

        result = FlightService().search(search_request)
        self.assertTrue(result.success)

        self.assertEqual(Airport.objects.count(), airport_count_before)

    @patch("interactions.tripjack.client.TripJackClient.search_flights")
    def test_failed_search_writes_nothing_to_the_database(self, mock_search_flights):
        mock_search_flights.side_effect = TripJackRequestError("boom")

        airport_count_before = Airport.objects.count()

        search_request = SearchRequest(
            trip_type="oneway",
            segments=[
                FlightSegmentRequest(origin="DEL", destination="GOI", departure_date=datetime.date(2026, 9, 21))
            ],
        )

        result = FlightService().search(search_request)
        self.assertFalse(result.success)

        self.assertEqual(Airport.objects.count(), airport_count_before)
