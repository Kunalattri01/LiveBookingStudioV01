import unittest

from flight.normalizers.tripjack_booking import TripJackBookingNormalizer


class TripJackBookingNormalizerTests(unittest.TestCase):
    def setUp(self):
        self.normalizer = TripJackBookingNormalizer()

    def test_seat_map_normalizes_only_explicit_availability(self):
        raw = {
            "bookingId": "BOOK-1",
            "aircraftType": "A320",
            "seat": [
                {"seatNo": "1A", "isAvailable": True, "price": 500, "seatType": "WINDOW"},
                {"seatNo": "1B", "isAvailable": False, "price": 0, "seatType": "MIDDLE"},
                {"seatNo": "1C", "status": "available", "price": 300},
                {"seatNo": "2A", "status": "blocked", "price": 0},
                {"seatNo": "2B", "price": 250},
            ],
        }

        result = self.normalizer.normalize_seat_map(raw)

        self.assertEqual(result.booking_id, "BOOK-1")
        self.assertEqual(result.aircraft, "A320")
        self.assertEqual(result.available_seats, 2)
        self.assertEqual(result.unavailable_seats, 2)
        self.assertTrue(result.availability_known)
        self.assertEqual(len(result.seats), 5)
        self.assertEqual(result.seats[0].code, "1A")
        self.assertEqual(result.seats[0].row, 1)
        self.assertEqual(result.seats[0].column, "A")
        self.assertIsNone(result.seats[-1].available)
        self.assertFalse(result.seats[-1].availability_known)

    def test_seat_map_deduplicates_same_seat(self):
        raw = {"seats": [{"code": "12A", "available": True}, {"code": "12A", "available": True}]}
        result = self.normalizer.normalize_seat_map(raw)
        self.assertEqual(len(result.seats), 1)

    def test_review_exposes_supplier_seat_inventory_when_present(self):
        raw = {
            "bookingId": "BOOK-2",
            "status": {"success": True},
            "fareDetails": {"ADULT": {"sR": 9}},
        }
        result = self.normalizer.normalize_review(raw)
        self.assertEqual(result.booking_id, "BOOK-2")
        self.assertEqual(result.seats_available, 9)

    def test_unknown_seat_status_is_not_converted_to_available(self):
        result = self.normalizer.normalize_seat_map({"seat": [{"code": "20A", "status": "held"}]})
        self.assertIsNone(result.seats[0].available)
        self.assertFalse(result.seats[0].availability_known)


    def test_tripjack_seat_map_uses_is_booked_and_nested_seat_position(self):
        raw = {
            "seatInfo": {
                "seats": [
                    {
                        "seatNo": "3C",
                        "seatPosition": {"row": 3, "column": 3},
                        "isBooked": False,
                        "isAisle": True,
                        "code": "3C",
                        "amount": 799,
                    },
                    {
                        "seatNo": "4A",
                        "seatPosition": {"row": 4, "column": 1},
                        "isBooked": True,
                        "isAisle": False,
                        "code": "4A",
                        "amount": 300,
                    },
                ]
            },
            "bookingId": "TEST-BOOKING",
        }

        result = TripJackBookingNormalizer().normalize_seat_map(raw)

        self.assertEqual(result.available_seats, 1)
        self.assertEqual(result.unavailable_seats, 1)
        self.assertTrue(result.availability_known)

        available = next(seat for seat in result.seats if seat.code == "3C")
        booked = next(seat for seat in result.seats if seat.code == "4A")

        self.assertTrue(available.available)
        self.assertEqual(available.row, 3)
        self.assertEqual(available.column, "3")
        self.assertEqual(available.price, 799.0)

        self.assertFalse(booked.available)
        self.assertEqual(booked.row, 4)
        self.assertEqual(booked.column, "1")
