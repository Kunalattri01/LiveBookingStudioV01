import json
import os

from django.test import SimpleTestCase

from flight.normalizers.tripjack import TripJackNormalizationError, TripJackNormalizer

FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__), "fixtures", "tripjack_air_search_all_sample.json"
)


def load_fixture():
    with open(FIXTURE_PATH) as f:
        return json.load(f)


class TripJackNormalizerRealResponseTests(SimpleTestCase):
    """
    Uses a real, verified TripJack UAT air-search-all response
    (captured via Postman by the project owner - no secrets in the
    fixture) as the source of truth for field mapping.
    """

    def setUp(self):
        self.raw_response = load_fixture()
        self.flights = TripJackNormalizer().normalize(self.raw_response)

    def test_normalizes_multiple_flights(self):
        # Fixture contains 2 ONWARD itineraries.
        self.assertEqual(len(self.flights), 2)

    def test_first_flight_segment_fields(self):
        flight = self.flights[0]
        self.assertEqual(flight.provider, "tripjack")
        self.assertEqual(len(flight.segments), 1)

        segment = flight.segments[0]
        self.assertEqual(segment.segment_id, "142")
        self.assertEqual(segment.airline_code, "6E")
        self.assertEqual(segment.airline_name, "IndiGo")
        self.assertTrue(segment.is_lcc)
        self.assertEqual(segment.flight_number, "5341")
        self.assertEqual(segment.aircraft_type, "321")
        self.assertEqual(segment.origin, "DEL")
        self.assertEqual(segment.origin_city, "Delhi")
        self.assertEqual(segment.origin_terminal, "Terminal 3")
        self.assertEqual(segment.destination, "GOI")
        self.assertEqual(segment.destination_city, "Goa In")
        self.assertEqual(segment.departure_time, "2026-09-21T05:10")
        self.assertEqual(segment.arrival_time, "2026-09-21T07:40")
        self.assertEqual(segment.duration_minutes, 150)
        self.assertEqual(segment.technical_stops, 0)

    def test_first_flight_has_multiple_fares(self):
        flight = self.flights[0]
        self.assertEqual(len(flight.fares), 4)

        fare_types = {fare.fare_type for fare in flight.fares}
        self.assertEqual(fare_types, {"UPFRONT", "PUBLISHED", "CORPORATE", "SME"})

    def test_fare_price_breakdown_mapped_correctly(self):
        flight = self.flights[0]
        upfront_fare = next(f for f in flight.fares if f.fare_type == "UPFRONT")

        self.assertEqual(upfront_fare.base_fare, 7325.00)
        self.assertEqual(upfront_fare.taxes, 2585.50)
        self.assertEqual(upfront_fare.total_fare, 9910.50)
        self.assertEqual(upfront_fare.net_fare, 9910.50)
        self.assertEqual(upfront_fare.cabin_class, "ECONOMY")
        self.assertEqual(upfront_fare.booking_class, "O")
        self.assertEqual(upfront_fare.fare_basis, "RLIP")
        self.assertEqual(upfront_fare.seats_available, 9)
        self.assertEqual(upfront_fare.meal_included, False)
        self.assertEqual(upfront_fare.fare_id, "5-0019138363_0DELGOI6E5341~1211081761086558")

    def test_baggage_mapped_correctly(self):
        flight = self.flights[0]
        fare = flight.fares[0]

        self.assertIsNotNone(fare.baggage)
        self.assertEqual(fare.baggage.checkin, "15 Kg (01 Piece only)")
        self.assertEqual(fare.baggage.cabin, "7 Kg")

    def test_refund_type_is_passed_through_raw_not_guessed(self):
        """
        The 'rT' field's true/false semantics are not documented, so
        the normalizer must never translate it into `refundable`
        (True/False) - only pass through the raw code.
        """
        flight = self.flights[0]
        fare = flight.fares[0]

        self.assertIsNone(fare.refundable)
        self.assertEqual(fare.refund_type_code, 1)

    def test_currency_and_fare_rules_are_none_when_absent_from_response(self):
        """
        Neither field exists anywhere in the verified sample response,
        so both must stay None - never invented (e.g. assuming INR).
        """
        flight = self.flights[0]
        fare = flight.fares[0]

        self.assertIsNone(fare.currency)
        self.assertIsNone(fare.fare_rules_reference)

    def test_missing_optional_fields_handled_gracefully(self):
        """
        The second fixture itinerary (Air India, DEL->GOX with oaa=GOI)
        has no terminal on the arrival airport and only one fare with
        no 'mI' key present at all - the normalizer must not crash and
        must leave those fields as None rather than guessing.
        """
        second_flight = self.flights[1]
        segment = second_flight.segments[0]

        self.assertIsNone(segment.destination_terminal)

        fare = second_flight.fares[0]
        self.assertIsNone(fare.meal_included)
        self.assertEqual(fare.refund_type_code, 0)

    def test_stops_and_total_duration_computed_from_segments(self):
        flight = self.flights[0]
        self.assertEqual(flight.stops, 0)  # single segment -> 0 connections
        self.assertEqual(flight.total_duration_minutes, 150)

    def test_provider_reference_built_from_segment_ids(self):
        flight = self.flights[0]
        self.assertEqual(flight.provider_reference, "142")

    def test_malformed_response_raises_normalization_error(self):
        with self.assertRaises(TripJackNormalizationError):
            TripJackNormalizer().normalize({"unexpected": "shape"})

    def test_empty_onward_list_returns_empty_flight_list(self):
        empty_response = {"searchResult": {"tripInfos": {"ONWARD": []}}}
        flights = TripJackNormalizer().normalize(empty_response)
        self.assertEqual(flights, [])


class TripJackNormalizerMultiLegGeneralizationTests(SimpleTestCase):
    """
    Uses a CONSTRUCTED (not captured) fixture with a second leg key
    ("RETURN") to verify the normalizer correctly handles whatever
    leg keys TripJack actually returns, without hardcoding "RETURN"
    as a guess. This does NOT verify that "RETURN" is the real key
    name TripJack uses - only that the generalization logic itself
    works correctly for however many leg keys are present.
    """

    MULTILEG_FIXTURE_PATH = os.path.join(
        os.path.dirname(__file__), "fixtures", "tripjack_multileg_constructed_sample.json"
    )

    def setUp(self):
        with open(self.MULTILEG_FIXTURE_PATH) as f:
            self.raw_response = json.load(f)
        self.flights = TripJackNormalizer().normalize(self.raw_response)

    def test_normalizes_flights_from_every_leg_key(self):
        self.assertEqual(len(self.flights), 2)

    def test_leg_label_reflects_actual_response_key(self):
        leg_labels = {flight.leg_label for flight in self.flights}
        self.assertEqual(leg_labels, {"ONWARD", "RETURN"})

    def test_each_leg_normalized_independently_with_own_fare(self):
        onward = next(f for f in self.flights if f.leg_label == "ONWARD")
        ret = next(f for f in self.flights if f.leg_label == "RETURN")

        self.assertEqual(onward.segments[0].origin, "DEL")
        self.assertEqual(onward.segments[0].destination, "GOI")
        self.assertEqual(ret.segments[0].origin, "GOI")
        self.assertEqual(ret.segments[0].destination, "DEL")

        self.assertEqual(onward.fares[0].total_fare, 9910.50)
        self.assertEqual(ret.fares[0].total_fare, 10555.00)
