from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from interactions.tripjack.client import TripJackClient
from interactions.tripjack.exceptions import TripJackNotConfiguredError, TripJackRequestError


@override_settings(TRIPJACK_API_KEY="test-key-not-real", TRIPJACK_BASE_URL="https://apitest.tripjack.com")
class TripJackClientTests(TestCase):
    """
    Every test here mocks the HTTP layer (requests.post) - none of
    these make a real network call, and none use the real API key
    (a clearly fake value is used via override_settings).
    """

    def _mock_response(self, status_code=200, json_data=None, raise_json_error=False):
        response = Mock()
        response.status_code = status_code
        if raise_json_error:
            response.json.side_effect = ValueError("not json")
        else:
            response.json.return_value = json_data or {}
        return response

    @patch("requests.post")
    def test_successful_search_returns_parsed_json(self, mock_post):
        mock_post.return_value = self._mock_response(
            200, {"searchResult": {"tripInfos": {"ONWARD": []}}, "status": {"success": True}}
        )

        client = TripJackClient()
        result = client.search_flights({"searchQuery": {}})

        self.assertIn("searchResult", result)
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_apikey_header_sent_correctly(self, mock_post):
        mock_post.return_value = self._mock_response(
            200, {"searchResult": {}, "status": {"success": True}}
        )

        client = TripJackClient()
        client.search_flights({"searchQuery": {}})

        _, kwargs = mock_post.call_args
        self.assertIn("headers", kwargs)
        self.assertEqual(kwargs["headers"]["apikey"], "test-key-not-real")
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/json")

    @patch("requests.post")
    def test_correct_endpoint_called(self, mock_post):
        mock_post.return_value = self._mock_response(
            200, {"searchResult": {}, "status": {"success": True}}
        )

        client = TripJackClient()
        client.search_flights({"searchQuery": {}})

        args, _ = mock_post.call_args
        self.assertEqual(args[0], "https://apitest.tripjack.com/fms/v1/air-search-all")

    @patch("requests.post")
    def test_non_200_status_raises_request_error(self, mock_post):
        mock_post.return_value = self._mock_response(500)

        client = TripJackClient()
        with self.assertRaises(TripJackRequestError):
            client.search_flights({"searchQuery": {}})

    @patch("requests.post")
    def test_malformed_json_raises_request_error(self, mock_post):
        mock_post.return_value = self._mock_response(200, raise_json_error=True)

        client = TripJackClient()
        with self.assertRaises(TripJackRequestError):
            client.search_flights({"searchQuery": {}})

    @patch("requests.post")
    def test_unsuccessful_status_block_raises_request_error(self, mock_post):
        mock_post.return_value = self._mock_response(
            200, {"searchResult": {}, "status": {"success": False}}
        )

        client = TripJackClient()
        with self.assertRaises(TripJackRequestError):
            client.search_flights({"searchQuery": {}})

    @patch("requests.post")
    def test_missing_status_block_raises_request_error(self, mock_post):
        mock_post.return_value = self._mock_response(200, {"searchResult": {}})

        client = TripJackClient()
        with self.assertRaises(TripJackRequestError):
            client.search_flights({"searchQuery": {}})

    @patch("requests.post")
    def test_timeout_raises_request_error(self, mock_post):
        import requests

        mock_post.side_effect = requests.Timeout("timed out")

        client = TripJackClient()
        with self.assertRaises(TripJackRequestError):
            client.search_flights({"searchQuery": {}})

    @patch("requests.post")
    def test_connection_error_raises_request_error(self, mock_post):
        import requests

        mock_post.side_effect = requests.ConnectionError("connection refused")

        client = TripJackClient()
        with self.assertRaises(TripJackRequestError):
            client.search_flights({"searchQuery": {}})


@override_settings(TRIPJACK_API_KEY="", TRIPJACK_BASE_URL="")
class TripJackClientNotConfiguredTests(TestCase):
    def test_missing_config_raises_not_configured_error(self):
        client = TripJackClient()
        with self.assertRaises(TripJackNotConfiguredError):
            client.search_flights({"searchQuery": {}})

@override_settings(
    TRIPJACK_API_KEY="test-key-not-real",
    TRIPJACK_BASE_URL="https://apitest.tripjack.com",
    TRIPJACK_TIMEOUT_SECONDS=37,
)
class TripJackClientBookingTests(TestCase):
    @patch("requests.post")
    def test_review_uses_configured_timeout_and_price_ids(self, mock_post):
        response = Mock(status_code=200)
        response.json.return_value = {"bookingId": "TEST-BOOKING"}
        mock_post.return_value = response

        TripJackClient().review_fares(["PRICE-1", "PRICE-2"])
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://apitest.tripjack.com/fms/v1/review")
        self.assertEqual(kwargs["json"], {"priceIds": ["PRICE-1", "PRICE-2"]})
        self.assertEqual(kwargs["timeout"], 37)

    @patch("requests.post")
    def test_seat_map_uses_booking_id(self, mock_post):
        response = Mock(status_code=200)
        response.json.return_value = {"seat": []}
        mock_post.return_value = response

        TripJackClient().seat_map("TEST-BOOKING")
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://apitest.tripjack.com/fms/v1/seat")
        self.assertEqual(kwargs["json"], {"bookingId": "TEST-BOOKING"})
