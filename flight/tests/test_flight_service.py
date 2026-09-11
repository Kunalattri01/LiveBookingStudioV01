import datetime

from django.test import TestCase, override_settings

from flight.providers.mock_provider import MockFlightProvider
from flight.services.dto import FlightSegmentRequest, SearchRequest
from flight.services.flight_service import FlightService


class FlightServiceWithMockProviderTests(TestCase):
    """
    These tests explicitly construct MockFlightProvider and inject it -
    exactly the only sanctioned way to use it. FlightService is never
    given a chance to reach it through configuration here.
    """

    def setUp(self):
        self.tomorrow = datetime.date.today() + datetime.timedelta(days=5)
        self.search_request = SearchRequest(
            trip_type="oneway",
            segments=[FlightSegmentRequest(origin="DEL", destination="BLR", departure_date=self.tomorrow)],
        )

    def test_mock_provider_returns_flights(self):
        service = FlightService(provider=MockFlightProvider())
        result = service.search(self.search_request)

        self.assertTrue(result.success)
        self.assertEqual(len(result.flights), 1)
        self.assertEqual(result.flights[0].provider, "mock")
        self.assertTrue(result.flights[0].provider_reference.startswith("MOCK-"))

    def test_mock_provider_flight_has_fare(self):
        service = FlightService(provider=MockFlightProvider())
        result = service.search(self.search_request)

        flight = result.flights[0]
        self.assertEqual(len(flight.fares), 1)
        self.assertIsNotNone(flight.fares[0].total_fare)


class FlightServiceDefaultProviderTests(TestCase):
    """
    These tests do NOT inject a provider - FlightService must fall
    through to SupplierManager. FLIGHT_PROVIDER is explicitly
    overridden to "unconfigured" here rather than relying on whatever
    happens to be set in the local .env, so this test is deterministic
    and never makes a real network call regardless of local
    configuration.
    """

    def setUp(self):
        self.tomorrow = datetime.date.today() + datetime.timedelta(days=5)
        self.search_request = SearchRequest(
            trip_type="oneway",
            segments=[FlightSegmentRequest(origin="DEL", destination="BLR", departure_date=self.tomorrow)],
        )

    @override_settings(FLIGHT_PROVIDER="unconfigured")
    def test_default_provider_returns_controlled_error(self):
        service = FlightService()
        result = service.search(self.search_request)

        self.assertFalse(result.success)
        self.assertEqual(result.flights, [])
        self.assertEqual(result.error_code, "flight_provider_not_configured")
        self.assertIsNotNone(result.error_message)
