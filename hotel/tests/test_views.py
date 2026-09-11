from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from hotel.models import Hotel

CHECK_IN = (date.today() + timedelta(days=10)).isoformat()
CHECK_OUT = (date.today() + timedelta(days=12)).isoformat()


class HotelSearchViewTests(TestCase):
    def test_valid_search_redirects_to_listing(self):
        response = self.client.get(
            reverse("HotelSearchPage"),
            {"destination": "Delhi", "checkin": CHECK_IN, "checkout": CHECK_OUT, "guests": "2", "rooms": "1"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/hotel/hotel-listing/", response.url)

    def test_missing_destination_redirects_home_with_error(self):
        response = self.client.get(reverse("HotelSearchPage"), {"checkin": CHECK_IN, "checkout": CHECK_OUT})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/?search_error="))


class HotelListingViewTests(TestCase):
    def setUp(self):
        Hotel.objects.update_or_create(
            tj_hotel_id="10000000012345",
            defaults={"name": "Pride Plaza Hotel Aerocity New Delhi", "city": "Delhi", "is_popular": True, "is_active": True},
        )

    def test_valid_search_renders_page(self):
        response = self.client.get(
            reverse("HotelListingPage"),
            {"destination": "Delhi", "checkin": CHECK_IN, "checkout": CHECK_OUT, "guests": "2", "rooms": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "hotel-listing.js")
        self.assertContains(response, "__HOTEL_SEARCH_REQUEST__")

    def test_unknown_destination_redirects_home_with_error(self):
        response = self.client.get(
            reverse("HotelListingPage"),
            {"destination": "Nowhereville", "checkin": CHECK_IN, "checkout": CHECK_OUT},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/?search_error="))


class HotelDetailViewTests(TestCase):
    def test_valid_detail_request_renders_page(self):
        response = self.client.get(
            reverse("HotelDetailPage"),
            {
                "hid": "10000000012345",
                "correlation_id": "corr-1",
                "checkin": CHECK_IN,
                "checkout": CHECK_OUT,
                "rooms_json": '[{"adults": 2}]',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "hotel-detail.js")
        self.assertContains(response, "__HOTEL_DETAIL_REQUEST__")

    def test_missing_correlation_id_redirects_home_with_error(self):
        response = self.client.get(
            reverse("HotelDetailPage"), {"hid": "10000000012345", "checkin": CHECK_IN, "checkout": CHECK_OUT}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/?search_error="))


class HotelBookingViewTests(TestCase):
    def test_without_review_redirects_home(self):
        response = self.client.get(reverse("HotelBookingPage"))
        self.assertEqual(response.status_code, 302)

    def test_with_review_in_session_renders_page(self):
        session = self.client.session
        session["hotel_review"] = {
            "booking_id": "TGS1",
            "hotel_name": "Pride Plaza",
            "option": {
                "option_id": "opt-1",
                "room_info": [{"id": "r1", "name": "Deluxe"}],
                "meal_basis": "Room Only",
                "pricing": {"total_price": 1000, "base_price": 1000, "taxes": 0, "mf": 0, "mft": 0, "currency": "INR"},
            },
        }
        session.save()

        response = self.client.get(reverse("HotelBookingPage"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "hotel-booking.js")


class HotelConfirmationViewTests(TestCase):
    def test_without_book_result_redirects_home(self):
        response = self.client.get(reverse("HotelConfirmationPage"))
        self.assertEqual(response.status_code, 302)

    def test_with_book_result_in_session_renders_page(self):
        session = self.client.session
        session["hotel_book_result"] = {"booking_id": "TJ1", "accepted": True}
        session.save()

        response = self.client.get(reverse("HotelConfirmationPage"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "hotel-confirmation.js")
