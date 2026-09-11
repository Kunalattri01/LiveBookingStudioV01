from unittest.mock import Mock, patch

import requests
from django.test import SimpleTestCase, override_settings

from hotel.providers.tripjack_client import TripJackHotelClient
from hotel.providers.tripjack_exceptions import TripJackHotelNotConfiguredError, TripJackHotelRequestError


def _mock_response(status_code=200, json_data=None, raise_json_error=False):
    response = Mock()
    response.status_code = status_code
    if raise_json_error:
        response.json.side_effect = ValueError("not json")
    else:
        response.json.return_value = json_data if json_data is not None else {}
    return response


@override_settings(
    TRIPJACK_API_KEY="test-key-not-real",
    HOTEL_HMS_BASE_URL="https://apitest-hms.tripjack.com",
    HOTEL_BOOKER_BASE_URL="https://apitest-hotel-booker.tripjack.com",
    TRIPJACK_TIMEOUT_SECONDS=37,
)
class TripJackHotelClientTests(SimpleTestCase):
    def test_not_configured_raises_without_network_call(self):
        with override_settings(TRIPJACK_API_KEY=""):
            client = TripJackHotelClient()
            with self.assertRaises(TripJackHotelNotConfiguredError):
                client.listing({"checkIn": "2026-05-25"})

    @patch("requests.post")
    def test_listing_posts_to_hms_base_url_with_apikey_header(self, mock_post):
        mock_post.return_value = _mock_response(json_data={"hotels": [], "status": {"success": True}})
        payload = {"checkIn": "2026-05-25", "checkOut": "2026-05-26"}

        result = TripJackHotelClient().listing(payload)

        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://apitest-hms.tripjack.com/hms/v3/hotel/listing")
        self.assertEqual(kwargs["headers"]["apikey"], "test-key-not-real")
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/json")
        self.assertEqual(kwargs["json"], payload)
        self.assertEqual(kwargs["timeout"], 37)
        self.assertEqual(result, {"hotels": [], "status": {"success": True}})

    @patch("requests.post")
    def test_pricing_posts_to_hms_pricing_path(self, mock_post):
        mock_post.return_value = _mock_response(json_data={"options": []})
        TripJackHotelClient().pricing({"hid": "10000000012345"})
        args, _ = mock_post.call_args
        self.assertEqual(args[0], "https://apitest-hms.tripjack.com/hms/v3/hotel/pricing")

    @patch("requests.post")
    def test_review_posts_to_hms_review_path(self, mock_post):
        mock_post.return_value = _mock_response(json_data={"option": {}})
        TripJackHotelClient().review({"optionId": "abc"})
        args, _ = mock_post.call_args
        self.assertEqual(args[0], "https://apitest-hms.tripjack.com/hms/v3/hotel/review")

    @patch("requests.post")
    def test_book_posts_to_booker_base_url(self, mock_post):
        mock_post.return_value = _mock_response(json_data={"bookingId": "TJ1", "status": {"success": True}})
        TripJackHotelClient().book({"bookingId": "TGS1"})
        args, _ = mock_post.call_args
        self.assertEqual(args[0], "https://apitest-hotel-booker.tripjack.com/oms/v3/hotel/book")

    @patch("requests.post")
    def test_booking_details_posts_booking_id(self, mock_post):
        mock_post.return_value = _mock_response(json_data={"order": {}})
        TripJackHotelClient().booking_details("TJ1")
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://apitest-hotel-booker.tripjack.com/oms/v3/hotel/booking-details")
        self.assertEqual(kwargs["json"], {"bookingId": "TJ1"})

    def test_booking_details_requires_booking_id(self):
        with self.assertRaises(TripJackHotelRequestError):
            TripJackHotelClient().booking_details("")

    @patch("requests.post")
    def test_timeout_is_wrapped(self, mock_post):
        mock_post.side_effect = requests.Timeout("boom")
        with self.assertRaises(TripJackHotelRequestError):
            TripJackHotelClient().listing({})

    @patch("requests.post")
    def test_connection_error_is_wrapped(self, mock_post):
        mock_post.side_effect = requests.ConnectionError("boom")
        with self.assertRaises(TripJackHotelRequestError):
            TripJackHotelClient().listing({})

    @patch("requests.post")
    def test_non_200_status_raises(self, mock_post):
        mock_post.return_value = _mock_response(status_code=500)
        with self.assertRaises(TripJackHotelRequestError):
            TripJackHotelClient().listing({})

    @patch("requests.post")
    def test_non_json_response_raises(self, mock_post):
        mock_post.return_value = _mock_response(raise_json_error=True)
        with self.assertRaises(TripJackHotelRequestError):
            TripJackHotelClient().listing({})
