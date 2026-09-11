import datetime

from django.test import TestCase

from flight.services.validators import validate_search_payload


class ValidatorsOneWayRoundTripTests(TestCase):
    def setUp(self):
        self.tomorrow = (datetime.date.today() + datetime.timedelta(days=5)).isoformat()
        self.later = (datetime.date.today() + datetime.timedelta(days=10)).isoformat()
        self.yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

    def test_valid_oneway(self):
        search_request, errors = validate_search_payload({
            "trip_type": "oneway",
            "origin": "DEL",
            "destination": "BLR",
            "departure_date": self.tomorrow,
            "adults": 1,
        })
        self.assertEqual(errors, [])
        self.assertEqual(search_request.trip_type, "oneway")
        self.assertEqual(search_request.origin, "DEL")
        self.assertEqual(search_request.destination, "BLR")
        self.assertEqual(len(search_request.segments), 1)

    def test_valid_roundtrip(self):
        search_request, errors = validate_search_payload({
            "trip_type": "roundtrip",
            "origin": "DEL",
            "destination": "BOM",
            "departure_date": self.tomorrow,
            "return_date": self.later,
        })
        self.assertEqual(errors, [])
        self.assertEqual(len(search_request.segments), 2)
        self.assertEqual(search_request.return_date.isoformat(), self.later)

    def test_unknown_airport_code_rejected(self):
        _, errors = validate_search_payload({
            "trip_type": "oneway",
            "origin": "XXX",
            "destination": "BLR",
            "departure_date": self.tomorrow,
        })
        self.assertTrue(any("Unknown" in e for e in errors))

    def test_same_origin_destination_rejected(self):
        _, errors = validate_search_payload({
            "trip_type": "oneway",
            "origin": "DEL",
            "destination": "DEL",
            "departure_date": self.tomorrow,
        })
        self.assertTrue(any("cannot be the same" in e for e in errors))

    def test_past_departure_date_rejected(self):
        _, errors = validate_search_payload({
            "trip_type": "oneway",
            "origin": "DEL",
            "destination": "BLR",
            "departure_date": self.yesterday,
        })
        self.assertTrue(any("cannot be in the past" in e for e in errors))

    def test_roundtrip_missing_return_date_rejected(self):
        _, errors = validate_search_payload({
            "trip_type": "roundtrip",
            "origin": "DEL",
            "destination": "BOM",
            "departure_date": self.tomorrow,
        })
        self.assertTrue(any("return date" in e for e in errors))

    def test_infants_exceed_adults_rejected(self):
        _, errors = validate_search_payload({
            "trip_type": "oneway",
            "origin": "DEL",
            "destination": "BLR",
            "departure_date": self.tomorrow,
            "adults": 1,
            "infants": 2,
        })
        self.assertTrue(any("Infants cannot exceed" in e for e in errors))

    def test_invalid_cabin_class_rejected(self):
        _, errors = validate_search_payload({
            "trip_type": "oneway",
            "origin": "DEL",
            "destination": "BLR",
            "departure_date": self.tomorrow,
            "cabin_class": "super-secret-class",
        })
        self.assertTrue(any("cabin class" in e.lower() for e in errors))


class ValidatorsMultiCityTests(TestCase):
    def setUp(self):
        self.day1 = (datetime.date.today() + datetime.timedelta(days=3)).isoformat()
        self.day2 = (datetime.date.today() + datetime.timedelta(days=6)).isoformat()
        self.day3 = (datetime.date.today() + datetime.timedelta(days=9)).isoformat()

    def test_valid_multicity(self):
        search_request, errors = validate_search_payload({
            "trip_type": "multicity",
            "segments": [
                {"origin": "DEL", "destination": "BOM", "departure_date": self.day1},
                {"origin": "BOM", "destination": "BLR", "departure_date": self.day2},
                {"origin": "BLR", "destination": "DEL", "departure_date": self.day3},
            ],
        })
        self.assertEqual(errors, [])
        self.assertEqual(len(search_request.segments), 3)

    def test_multicity_requires_at_least_two_segments(self):
        _, errors = validate_search_payload({
            "trip_type": "multicity",
            "segments": [
                {"origin": "DEL", "destination": "BOM", "departure_date": self.day1},
            ],
        })
        self.assertTrue(any("at least two segments" in e for e in errors))

    def test_multicity_segment_dates_must_be_chronological(self):
        _, errors = validate_search_payload({
            "trip_type": "multicity",
            "segments": [
                {"origin": "DEL", "destination": "BOM", "departure_date": self.day2},
                {"origin": "BOM", "destination": "BLR", "departure_date": self.day1},
            ],
        })
        self.assertTrue(any("cannot be before the previous segment" in e for e in errors))

    def test_multicity_too_many_segments_rejected(self):
        segments = [
            {"origin": "DEL", "destination": "BOM", "departure_date": self.day1}
            for _ in range(7)
        ]
        _, errors = validate_search_payload({
            "trip_type": "multicity",
            "segments": segments,
        })
        self.assertTrue(any("maximum of 6 segments" in e for e in errors))
