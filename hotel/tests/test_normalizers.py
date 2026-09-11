import unittest

from hotel.normalizers.tripjack import TripJackHotelNormalizationError, TripJackHotelNormalizer
from hotel.normalizers.tripjack_booking import TripJackHotelBookingNormalizationError, TripJackHotelBookingNormalizer

LISTING_RESPONSE = {
    "correlationId": "1p6IYhwDQ9NGwiZ8FaigQz",
    "nationality": "106",
    "currency": "INR",
    "totalResults": 5957,
    "hotels": [
        {
            "tjHotelId": "10000000012345",
            "name": "Pride Plaza Hotel Aerocity New Delhi",
            "options": [
                {
                    "optionId": "db35a71a-4577-4740-8706-7d32e4c2ca4e",
                    "optionType": "SRSM",
                    "roomInfo": [{"id": "10019446051", "name": "Deluxe, 2 Twin"}],
                    "inclusions": ["String1", "String2"],
                    "mealBasis": "Room Only",
                    "pricing": {
                        "totalPrice": 27806.62,
                        "basePrice": 27806.62,
                        "discount": 0,
                        "taxes": 0,
                        "mf": 0,
                        "mft": 0,
                        "currency": "INR",
                    },
                    "commercial": {"type": "NET", "commission": 0},
                    "compliance": {"gstType": "NA", "panRequired": False, "passportRequired": False},
                    "cancellation": {
                        "isRefundable": True,
                        "penalties": [
                            {"from": "2026-02-10T19:07:00", "to": "2026-05-18T23:59:59", "amount": 0},
                            {"from": "2026-05-18T23:59:59", "to": "2026-05-26T00:00:00", "amount": 27759.42},
                        ],
                    },
                }
            ],
        }
    ],
    "status": {"success": True},
}

REVIEW_RESPONSE = {
    "correlationId": "1p6IYhwDQ9NGwiZ8FaigQz",
    "tjHotelId": "10000000012345",
    "hotelName": "Pride Plaza Hotel Aerocity New Delhi",
    "bookingId": "TGS208420065548",
    "option": {
        "optionId": "db35a71a-4577-4740-8706-7d32e4c2ca4e",
        "optionType": "SRSM",
        "roomInfo": [{"id": "10019446051", "name": "Deluxe, 2 Twin"}],
        "inclusions": [],
        "mealBasis": "Room Only",
        "bookingNotes": "Must print on screen.",
        "pricing": {"totalPrice": 27806.62, "basePrice": 27806.62, "discount": 0, "taxes": 0, "mf": 0, "mft": 0, "currency": "INR"},
        "commercial": {"type": "NET", "commission": 0},
        "compliance": {"gstType": "NA", "panRequired": False, "passportRequired": False},
        "cancellation": {"isRefundable": True, "penalties": []},
        "deadlineDateTime": "2026-10-20T23:59:59",
    },
    "onholdAllowed": "true",
    "status": {"success": True},
}

BOOK_RESPONSE = {"bookingId": "TJ202487947162", "status": {"success": True}, "metaInfo": {}}

BOOKING_DETAILS_RESPONSE = {
    "order": {
        "bookingId": "TJ2040174908940",
        "amount": 6234.55,
        "status": "ON_HOLD",
        "createdOn": "2026-05-23T11:17:29.164",
    },
    "itemInfos": {
        "HOTEL": {
            "hInfo": {
                "name": "RAMEE GUESTLINE HOTEL KHAR",
                "ops": [{"tp": 6234.55, "sc": "INR"}],
            }
        }
    },
    "hotelConfirmationNumber": "TJ2040174908940",
    "status": {"success": True, "httpStatus": 200},
}


class TripJackHotelNormalizerTests(unittest.TestCase):
    def setUp(self):
        self.normalizer = TripJackHotelNormalizer()

    def test_normalize_listing(self):
        result = self.normalizer.normalize_listing(LISTING_RESPONSE)

        self.assertEqual(result["correlation_id"], "1p6IYhwDQ9NGwiZ8FaigQz")
        self.assertEqual(result["total_results"], 5957)
        self.assertEqual(len(result["hotels"]), 1)

        hotel = result["hotels"][0]
        self.assertEqual(hotel.tj_hotel_id, "10000000012345")
        self.assertEqual(hotel.name, "Pride Plaza Hotel Aerocity New Delhi")

        option = hotel.options[0]
        self.assertEqual(option.option_id, "db35a71a-4577-4740-8706-7d32e4c2ca4e")
        self.assertEqual(option.option_type, "SRSM")
        self.assertEqual(option.room_info[0].name, "Deluxe, 2 Twin")
        self.assertEqual(option.pricing.total_price, 27806.62)
        self.assertEqual(option.commercial.type, "NET")
        self.assertEqual(option.compliance.gst_type, "NA")
        self.assertTrue(option.cancellation.is_refundable)
        self.assertEqual(len(option.cancellation.penalties), 2)
        self.assertEqual(option.cancellation.penalties[1].amount, 27759.42)

    def test_normalize_listing_accepts_live_hotelid_field_name(self):
        # Live TripJack sandbox returns "hotelId" in the Listing response,
        # not "tjHotelId" as the API reference documents - verified against
        # a real response for tjHotelId 100000078396 (Priya Living Flower
        # Valley, Gurugram).
        raw = {
            "correlationId": "corr-1",
            "totalResults": 1,
            "hotels": [{"hotelId": "100000078396", "name": "Priya Living Flower Valley", "options": []}],
        }
        result = self.normalizer.normalize_listing(raw)
        self.assertEqual(result["hotels"][0].tj_hotel_id, "100000078396")

    def test_normalize_listing_missing_hotels_key_raises(self):
        with self.assertRaises(TripJackHotelNormalizationError):
            self.normalizer.normalize_listing({"status": {"success": True}})

    def test_normalize_review(self):
        review = self.normalizer.normalize_review(REVIEW_RESPONSE)

        self.assertEqual(review.booking_id, "TGS208420065548")
        self.assertEqual(review.tj_hotel_id, "10000000012345")
        self.assertTrue(review.onhold_allowed)
        self.assertEqual(review.deadline_datetime, "2026-10-20T23:59:59")
        self.assertEqual(review.option.option_id, "db35a71a-4577-4740-8706-7d32e4c2ca4e")

    def test_normalize_detail_accepts_live_hotelid_field_name(self):
        raw = {"hotelId": "100000078396", "hotelName": "Priya Living Flower Valley", "options": []}
        detail = self.normalizer.normalize_detail(raw)
        self.assertEqual(detail.tj_hotel_id, "100000078396")

    def test_normalize_review_accepts_live_hotelid_field_name(self):
        raw = {
            "hotelId": "100000078396",
            "hotelName": "Priya Living Flower Valley",
            "bookingId": "TJ1",
            "option": {"optionId": "opt-1"},
        }
        review = self.normalizer.normalize_review(raw)
        self.assertEqual(review.tj_hotel_id, "100000078396")

    def test_normalize_review_missing_option_key_raises(self):
        with self.assertRaises(TripJackHotelNormalizationError):
            self.normalizer.normalize_review({"status": {"success": True}})


class TripJackHotelBookingNormalizerTests(unittest.TestCase):
    def setUp(self):
        self.normalizer = TripJackHotelBookingNormalizer()

    def test_normalize_book(self):
        result = self.normalizer.normalize_book(BOOK_RESPONSE)
        self.assertEqual(result.booking_id, "TJ202487947162")
        self.assertTrue(result.accepted)

    def test_normalize_booking_details(self):
        details = self.normalizer.normalize_booking_details(BOOKING_DETAILS_RESPONSE)
        self.assertEqual(details.booking_id, "TJ2040174908940")
        self.assertEqual(details.status, "ON_HOLD")
        self.assertEqual(details.amount, 6234.55)
        self.assertEqual(details.currency, "INR")
        self.assertEqual(details.hotel_name, "RAMEE GUESTLINE HOTEL KHAR")
        self.assertEqual(details.confirmation_number, "TJ2040174908940")
        self.assertEqual(details.raw, BOOKING_DETAILS_RESPONSE)

    def test_normalize_booking_details_missing_order_key_raises(self):
        with self.assertRaises(TripJackHotelBookingNormalizationError):
            self.normalizer.normalize_booking_details({"status": {"success": True}})
