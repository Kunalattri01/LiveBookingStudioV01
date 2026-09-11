from datetime import date, timedelta

from django.test import TestCase

from hotel.models import Hotel
from hotel.services import validators


class ValidateSearchPayloadTests(TestCase):
    def setUp(self):
        Hotel.objects.update_or_create(tj_hotel_id="10000000012345", defaults={**{"name": "Pride Plaza Hotel Aerocity New Delhi", "city": "Delhi", "is_popular": True}, "is_active": True})
        self.check_in = date.today() + timedelta(days=10)
        self.check_out = self.check_in + timedelta(days=2)

    def test_valid_payload_resolves_destination_to_hids(self):
        payload = {
            "destination": "Delhi",
            "check_in": self.check_in.isoformat(),
            "check_out": self.check_out.isoformat(),
            "rooms": [{"adults": 2, "children": 1, "child_ages": [5]}],
        }
        request, errors = validators.validate_search_payload(payload)

        self.assertEqual(errors, [])
        self.assertEqual(request.hids, ["10000000012345"])
        self.assertEqual(len(request.rooms), 1)
        self.assertEqual(request.rooms[0].adults, 2)
        self.assertEqual(request.rooms[0].child_ages, [5])
        self.assertTrue(request.correlation_id)

    def test_unknown_destination_produces_error(self):
        payload = {
            "destination": "Nowhereville",
            "check_in": self.check_in.isoformat(),
            "check_out": self.check_out.isoformat(),
        }
        _, errors = validators.validate_search_payload(payload)
        self.assertTrue(any("No properties found" in e for e in errors))

    def test_missing_destination_produces_error(self):
        payload = {"check_in": self.check_in.isoformat(), "check_out": self.check_out.isoformat()}
        _, errors = validators.validate_search_payload(payload)
        self.assertTrue(any("destination" in e for e in errors))

    def test_checkout_before_checkin_produces_error(self):
        payload = {
            "destination": "Delhi",
            "check_in": self.check_out.isoformat(),
            "check_out": self.check_in.isoformat(),
        }
        _, errors = validators.validate_search_payload(payload)
        self.assertTrue(any("after check-in" in e for e in errors))

    def test_checkin_in_past_produces_error(self):
        payload = {
            "destination": "Delhi",
            "check_in": (date.today() - timedelta(days=1)).isoformat(),
            "check_out": self.check_out.isoformat(),
        }
        _, errors = validators.validate_search_payload(payload)
        self.assertTrue(any("past" in e for e in errors))

    def test_legacy_guests_and_room_count_fallback(self):
        payload = {
            "destination": "Delhi",
            "check_in": self.check_in.isoformat(),
            "check_out": self.check_out.isoformat(),
            "guests": 5,
            "room_count": 2,
        }
        request, errors = validators.validate_search_payload(payload)
        self.assertEqual(errors, [])
        self.assertEqual(len(request.rooms), 2)
        self.assertEqual(sum(r.adults for r in request.rooms), 5)

    def test_child_without_matching_ages_produces_error(self):
        payload = {
            "destination": "Delhi",
            "check_in": self.check_in.isoformat(),
            "check_out": self.check_out.isoformat(),
            "rooms": [{"adults": 2, "children": 2, "child_ages": [5]}],
        }
        _, errors = validators.validate_search_payload(payload)
        self.assertTrue(any("one age" in e for e in errors))

    def test_explicit_hids_bypass_destination_resolution(self):
        payload = {
            "destination": "",
            "hids": ["10000000099999"],
            "check_in": self.check_in.isoformat(),
            "check_out": self.check_out.isoformat(),
        }
        request, errors = validators.validate_search_payload(payload)
        self.assertEqual(errors, [])
        self.assertEqual(request.hids, ["10000000099999"])


class ValidateDetailPayloadTests(TestCase):
    def setUp(self):
        self.check_in = date.today() + timedelta(days=10)
        self.check_out = self.check_in + timedelta(days=2)

    def test_valid_payload(self):
        payload = {
            "hid": "10000000012345",
            "correlation_id": "corr-1",
            "check_in": self.check_in.isoformat(),
            "check_out": self.check_out.isoformat(),
            "rooms": [{"adults": 1}],
        }
        request, errors = validators.validate_detail_payload(payload)
        self.assertEqual(errors, [])
        self.assertEqual(request.hid, "10000000012345")
        self.assertEqual(request.correlation_id, "corr-1")

    def test_missing_correlation_id_produces_error(self):
        payload = {
            "hid": "10000000012345",
            "check_in": self.check_in.isoformat(),
            "check_out": self.check_out.isoformat(),
        }
        _, errors = validators.validate_detail_payload(payload)
        self.assertTrue(any("correlation ID" in e for e in errors))


class ValidateReviewPayloadTests(TestCase):
    def test_valid_payload(self):
        payload = {
            "correlation_id": "corr-1",
            "option_id": "opt-1",
            "review_hash": "hash-1",
            "hid": "10000000012345",
        }
        request, errors = validators.validate_review_payload(payload)
        self.assertEqual(errors, [])
        self.assertEqual(request.option_id, "opt-1")

    def test_missing_fields_produce_errors(self):
        _, errors = validators.validate_review_payload({})
        self.assertEqual(len(errors), 4)


class ValidateBookPayloadTests(TestCase):
    def test_valid_payload(self):
        payload = {
            "booking_id": "TGS1",
            "room_traveller_info": [
                {
                    "travellers": [
                        {"title": "Mr", "passenger_type": "ADULT", "first_name": "Aryan", "last_name": "Singh"}
                    ]
                }
            ],
            "delivery_info": {"emails": ["a@example.com"], "contacts": ["9999999999"], "codes": ["+91"]},
            "amount": 1000,
        }
        request, errors = validators.validate_book_payload(payload)
        self.assertEqual(errors, [])
        self.assertEqual(request.amount, 1000.0)
        self.assertEqual(request.room_traveller_info[0].travellers[0].first_name, "Aryan")

    def test_missing_booking_id_produces_error(self):
        _, errors = validators.validate_book_payload({})
        self.assertTrue(any("booking ID" in e for e in errors))

    def test_invalid_email_produces_error(self):
        payload = {
            "booking_id": "TGS1",
            "room_traveller_info": [
                {"travellers": [{"title": "Mr", "passenger_type": "ADULT", "first_name": "A", "last_name": "B"}]}
            ],
            "delivery_info": {"emails": ["not-an-email"], "contacts": ["9999999999"], "codes": ["+91"]},
        }
        _, errors = validators.validate_book_payload(payload)
        self.assertTrue(any("valid email" in e for e in errors))

    def test_mismatched_contacts_and_codes_produces_error(self):
        payload = {
            "booking_id": "TGS1",
            "room_traveller_info": [
                {"travellers": [{"title": "Mr", "passenger_type": "ADULT", "first_name": "A", "last_name": "B"}]}
            ],
            "delivery_info": {"emails": ["a@example.com"], "contacts": ["9999999999"], "codes": []},
        }
        _, errors = validators.validate_book_payload(payload)
        self.assertTrue(any("dialing code" in e for e in errors))
