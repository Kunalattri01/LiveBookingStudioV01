import datetime
import json
from unittest.mock import patch

from django.test import TestCase, override_settings


class AirportApiTests(TestCase):
    def test_airport_search_empty_query_returns_results(self):
        response = self.client.get("/api/v1/airports/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("results", data)
        self.assertGreater(len(data["results"]), 0)

    def test_airport_search_filters_by_query(self):
        response = self.client.get("/api/v1/airports/?q=del")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        codes = [item["code"] for item in data["results"]]
        self.assertIn("DEL", codes)


@override_settings(FLIGHT_PROVIDER="unconfigured")
class FlightSearchApiUnconfiguredTests(TestCase):
    """
    FLIGHT_PROVIDER is explicitly forced to "unconfigured" for this
    class rather than relying on whatever the local .env happens to
    have set, so these tests are deterministic and never attempt a
    real network call.
    """

    def setUp(self):
        self.tomorrow = (datetime.date.today() + datetime.timedelta(days=5)).isoformat()

    def _post(self, payload):
        return self.client.post(
            "/api/v1/flights/search/",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_valid_oneway_search_returns_controlled_503_when_unconfigured(self):
        """
        With no provider configured, a structurally valid search must
        return a controlled 503 - never fabricated flight data.
        """
        response = self._post({
            "trip_type": "oneway",
            "origin": "DEL",
            "destination": "BLR",
            "departure_date": self.tomorrow,
            "adults": 1,
        })

        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error_code"], "flight_provider_not_configured")
        self.assertNotIn("flights", data)

    def test_invalid_airport_returns_400(self):
        response = self._post({
            "trip_type": "oneway",
            "origin": "XXX",
            "destination": "BLR",
            "departure_date": self.tomorrow,
        })

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error_code"], "invalid_search_request")

    def test_multicity_search_passes_validation_but_provider_unconfigured(self):
        day1 = (datetime.date.today() + datetime.timedelta(days=3)).isoformat()
        day2 = (datetime.date.today() + datetime.timedelta(days=6)).isoformat()

        response = self._post({
            "trip_type": "multicity",
            "segments": [
                {"origin": "DEL", "destination": "BOM", "departure_date": day1},
                {"origin": "BOM", "destination": "BLR", "departure_date": day2},
            ],
        })

        # No provider configured -> controlled 503, not a validation
        # error - proves multi-city passes validation successfully.
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertEqual(data["error_code"], "flight_provider_not_configured")

    def test_response_never_contains_tripjack_credentials(self):
        response = self._post({
            "trip_type": "oneway",
            "origin": "DEL",
            "destination": "BLR",
            "departure_date": self.tomorrow,
        })

        body = response.content.decode()
        self.assertNotIn("TRIPJACK_API_KEY", body)
        # The actual configured test key value must never appear either.
        from django.conf import settings

        if settings.TRIPJACK_API_KEY:
            self.assertNotIn(settings.TRIPJACK_API_KEY, body)


@override_settings(FLIGHT_PROVIDER="tripjack")
class FlightSearchApiTripJackMultiSegmentTests(TestCase):
    """
    With FLIGHT_PROVIDER=tripjack, round-trip/multi-city now build a
    real multi-route request (verified against the official TripJack
    collection) instead of being blocked. The HTTP layer is always
    mocked here - these tests never make a real network call.
    """

    def _load_fixture(self):
        import json as _json
        import os as _os

        fixture_path = _os.path.join(
            _os.path.dirname(__file__), "fixtures", "tripjack_air_search_all_sample.json"
        )
        with open(fixture_path) as f:
            return _json.load(f)

    def test_roundtrip_returns_200_with_mocked_tripjack(self):
        tomorrow = (datetime.date.today() + datetime.timedelta(days=5)).isoformat()
        later = (datetime.date.today() + datetime.timedelta(days=10)).isoformat()

        with patch("interactions.tripjack.client.TripJackClient.search_flights") as mock_search_flights:
            mock_search_flights.return_value = self._load_fixture()

            response = self.client.post(
                "/api/v1/flights/search/",
                data=json.dumps({
                    "trip_type": "roundtrip",
                    "origin": "DEL",
                    "destination": "GOI",
                    "departure_date": tomorrow,
                    "return_date": later,
                }),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["success"])

            sent_payload = mock_search_flights.call_args[0][0]
            self.assertEqual(len(sent_payload["searchQuery"]["routeInfos"]), 2)

    def test_multicity_returns_200_with_mocked_tripjack(self):
        day1 = (datetime.date.today() + datetime.timedelta(days=3)).isoformat()
        day2 = (datetime.date.today() + datetime.timedelta(days=6)).isoformat()

        with patch("interactions.tripjack.client.TripJackClient.search_flights") as mock_search_flights:
            mock_search_flights.return_value = self._load_fixture()

            response = self.client.post(
                "/api/v1/flights/search/",
                data=json.dumps({
                    "trip_type": "multicity",
                    "segments": [
                        {"origin": "DEL", "destination": "BOM", "departure_date": day1},
                        {"origin": "BOM", "destination": "GOI", "departure_date": day2},
                    ],
                }),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 200)
            sent_payload = mock_search_flights.call_args[0][0]
            self.assertEqual(len(sent_payload["searchQuery"]["routeInfos"]), 2)

    def test_roundtrip_provider_failure_returns_controlled_502(self):
        """
        If TripJack itself fails for a round-trip search, the error
        must still be the same controlled shape - never fake data.
        """
        from interactions.tripjack.exceptions import TripJackRequestError

        tomorrow = (datetime.date.today() + datetime.timedelta(days=5)).isoformat()
        later = (datetime.date.today() + datetime.timedelta(days=10)).isoformat()

        with patch("interactions.tripjack.client.TripJackClient.search_flights") as mock_search_flights:
            mock_search_flights.side_effect = TripJackRequestError("boom")

            response = self.client.post(
                "/api/v1/flights/search/",
                data=json.dumps({
                    "trip_type": "roundtrip",
                    "origin": "DEL",
                    "destination": "GOI",
                    "departure_date": tomorrow,
                    "return_date": later,
                }),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 502)
            data = response.json()
            self.assertFalse(data["success"])
            self.assertEqual(data["error_code"], "flight_provider_error")
