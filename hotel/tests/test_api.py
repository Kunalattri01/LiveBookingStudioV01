from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from hotel.models import Hotel

CHECK_IN = (date.today() + timedelta(days=10)).isoformat()
CHECK_OUT = (date.today() + timedelta(days=12)).isoformat()

LISTING_RAW = {
    "correlationId": "corr-1",
    "nationality": "106",
    "currency": "INR",
    "totalResults": 1,
    "hotels": [
        {
            "tjHotelId": "10000000012345",
            "name": "Pride Plaza Hotel Aerocity New Delhi",
            "options": [
                {
                    "optionId": "opt-1",
                    "optionType": "SRSM",
                    "roomInfo": [{"id": "r1", "name": "Deluxe"}],
                    "inclusions": [],
                    "mealBasis": "Room Only",
                    "pricing": {"totalPrice": 1000, "basePrice": 1000, "discount": 0, "taxes": 0, "mf": 0, "mft": 0, "currency": "INR"},
                    "commercial": {"type": "NET", "commission": 0},
                    "compliance": {"gstType": "NA", "panRequired": False, "passportRequired": False},
                    "cancellation": {"isRefundable": True, "penalties": []},
                }
            ],
        }
    ],
    "status": {"success": True},
}

PRICING_RAW = {
    "tjHotelId": "10000000012345",
    "hotelName": "Pride Plaza Hotel Aerocity New Delhi",
    "nationality": "106",
    "options": [LISTING_RAW["hotels"][0]["options"][0]],
    "reviewHash": "hash-1",
    "correlationId": "corr-1",
    "status": {"success": True},
}

REVIEW_RAW = {
    "correlationId": "corr-1",
    "tjHotelId": "10000000012345",
    "hotelName": "Pride Plaza Hotel Aerocity New Delhi",
    "bookingId": "TGS1",
    "option": PRICING_RAW["options"][0],
    "onholdAllowed": "true",
    "status": {"success": True},
}

BOOK_RAW = {"bookingId": "TJ1", "status": {"success": True}, "metaInfo": {}}
BOOKING_DETAILS_RAW = {
    "order": {"bookingId": "TJ1", "amount": 1000, "status": "CONFIRMED", "createdOn": "2026-05-23T11:17:29"},
    "itemInfos": {"HOTEL": {"hInfo": {"name": "Pride Plaza", "ops": [{"sc": "INR"}]}}},
    "hotelConfirmationNumber": "TJ1",
    "status": {"success": True},
}


@override_settings(
    HOTEL_PROVIDER="tripjack",
    TRIPJACK_API_KEY="test-key-not-real",
    HOTEL_HMS_BASE_URL="https://apitest-hms.tripjack.com",
    HOTEL_BOOKER_BASE_URL="https://apitest-hotel-booker.tripjack.com",
)
class HotelApiTests(TestCase):
    def setUp(self):
        Hotel.objects.update_or_create(tj_hotel_id="10000000012345", defaults={**{"name": "Pride Plaza Hotel Aerocity New Delhi", "city": "Delhi", "is_popular": True}, "is_active": True})

    @patch("hotel.providers.tripjack_client.TripJackHotelClient.listing")
    def test_listing_success(self, mock_listing):
        mock_listing.return_value = LISTING_RAW

        response = self.client.post(
            reverse("ApiHotelListing"),
            data={
                "destination": "Delhi",
                "check_in": CHECK_IN,
                "check_out": CHECK_OUT,
                "rooms": [{"adults": 2}],
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["hotels"]), 1)
        self.assertEqual(data["hotels"][0]["tj_hotel_id"], "10000000012345")

        sent_payload = mock_listing.call_args[0][0]
        self.assertEqual(sent_payload["hids"], [10000000012345])
        self.assertEqual(sent_payload["checkIn"], CHECK_IN)

    def test_listing_invalid_payload_returns_400(self):
        response = self.client.post(
            reverse("ApiHotelListing"),
            data={"destination": "Nowhereville", "check_in": CHECK_IN, "check_out": CHECK_OUT},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])
        self.assertEqual(response.json()["error_code"], "invalid_search_request")

    @override_settings(HOTEL_PROVIDER="unconfigured")
    def test_listing_returns_503_when_provider_not_configured(self):
        response = self.client.post(
            reverse("ApiHotelListing"),
            data={"destination": "Delhi", "check_in": CHECK_IN, "check_out": CHECK_OUT, "rooms": [{"adults": 1}]},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error_code"], "hotel_provider_not_configured")

    @patch("hotel.providers.tripjack_client.TripJackHotelClient.pricing")
    def test_pricing_success(self, mock_pricing):
        mock_pricing.return_value = PRICING_RAW

        response = self.client.post(
            reverse("ApiHotelPricing"),
            data={
                "hid": "10000000012345",
                "correlation_id": "corr-1",
                "check_in": CHECK_IN,
                "check_out": CHECK_OUT,
                "rooms": [{"adults": 2}],
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["detail"]["review_hash"], "hash-1")

    @patch("hotel.providers.tripjack_client.TripJackHotelClient.review")
    def test_review_success_stores_session(self, mock_review):
        mock_review.return_value = REVIEW_RAW

        response = self.client.post(
            reverse("ApiHotelReview"),
            data={"correlation_id": "corr-1", "option_id": "opt-1", "review_hash": "hash-1", "hid": "10000000012345"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["review"]["booking_id"], "TGS1")
        self.assertEqual(self.client.session["hotel_review"]["booking_id"], "TGS1")

    @patch("hotel.providers.tripjack_client.TripJackHotelClient.book")
    def test_book_success(self, mock_book):
        mock_book.return_value = BOOK_RAW

        response = self.client.post(
            reverse("ApiHotelBook"),
            data={
                "booking_id": "TGS1",
                "room_traveller_info": [
                    {"travellers": [{"title": "Mr", "passenger_type": "ADULT", "first_name": "Aryan", "last_name": "Singh"}]}
                ],
                "delivery_info": {"emails": ["a@example.com"], "contacts": ["9999999999"], "codes": ["+91"]},
                "amount": 1000,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["booking_id"], "TJ1")
        self.assertTrue(data["accepted"])

        sent_payload = mock_book.call_args[0][0]
        self.assertEqual(sent_payload["paymentInfos"], [{"amount": 1000.0}])
        self.assertEqual(sent_payload["roomTravellerInfo"][0]["travellerInfo"][0]["fN"], "Aryan")

    def test_book_invalid_payload_returns_400(self):
        response = self.client.post(reverse("ApiHotelBook"), data={}, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error_code"], "invalid_book_request")

    @patch("hotel.providers.tripjack_client.TripJackHotelClient.booking_details")
    def test_booking_details_success(self, mock_details):
        mock_details.return_value = BOOKING_DETAILS_RAW

        response = self.client.post(
            reverse("ApiHotelBookingDetails"), data={"booking_id": "TJ1"}, content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["details"]["status"], "CONFIRMED")

    def test_destination_autocomplete(self):
        response = self.client.get(reverse("ApiHotelDestinationSearch"), {"q": "del"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["cities"]), 1)
        self.assertEqual(data["cities"][0]["city"], "Delhi")
        self.assertEqual(data["cities"][0]["hotel_count"], 1)
        self.assertEqual(len(data["hotels"]), 1)
        self.assertEqual(data["hotels"][0]["tj_hotel_id"], "10000000012345")

    def test_destination_autocomplete_empty_query_returns_top_cities(self):
        response = self.client.get(reverse("ApiHotelDestinationSearch"), {"q": ""})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        city_names = [c["city"] for c in data["cities"]]
        self.assertIn("Delhi", city_names)
        self.assertEqual(data["hotels"], [])

    @patch("hotel.providers.tripjack_client.TripJackHotelClient.listing")
    def test_response_never_contains_tripjack_api_key(self, mock_listing):
        mock_listing.return_value = LISTING_RAW
        response = self.client.post(
            reverse("ApiHotelListing"),
            data={"destination": "Delhi", "check_in": CHECK_IN, "check_out": CHECK_OUT, "rooms": [{"adults": 1}]},
            content_type="application/json",
        )
        self.assertNotIn(b"test-key-not-real", response.content)


class HotelSearchNoPersistenceTests(TestCase):
    """
    Mirrors flight's TripJackSearchNoPersistenceTests: the search-side
    flow (listing/pricing/review) must never write to the DB, only
    read the local Hotel master table.
    """

    def setUp(self):
        Hotel.objects.update_or_create(tj_hotel_id="10000000012345", defaults={**{"name": "Pride Plaza Hotel Aerocity New Delhi", "city": "Delhi"}, "is_active": True})

    @override_settings(HOTEL_PROVIDER="tripjack", TRIPJACK_API_KEY="k", HOTEL_HMS_BASE_URL="https://x", HOTEL_BOOKER_BASE_URL="https://y")
    @patch("hotel.providers.tripjack_client.TripJackHotelClient.listing")
    def test_successful_listing_does_not_write_to_db(self, mock_listing):
        mock_listing.return_value = LISTING_RAW
        count_before = Hotel.objects.count()

        self.client.post(
            reverse("ApiHotelListing"),
            data={"destination": "Delhi", "check_in": CHECK_IN, "check_out": CHECK_OUT, "rooms": [{"adults": 1}]},
            content_type="application/json",
        )

        self.assertEqual(Hotel.objects.count(), count_before)
