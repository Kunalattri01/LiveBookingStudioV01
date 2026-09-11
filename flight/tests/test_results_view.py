import datetime
import json

from django.test import TestCase


class FlightResultsViewPayloadTests(TestCase):
    """
    These test the results VIEW (page shell + embedded search payload),
    not the live search itself - the live search now happens client
    side against /api/v1/flights/search/, covered by test_api.py.
    """

    def setUp(self):
        self.tomorrow = (datetime.date.today() + datetime.timedelta(days=5)).isoformat()
        self.later = (datetime.date.today() + datetime.timedelta(days=10)).isoformat()

    def _extract_payload(self, response):
        body = response.content.decode()
        marker = "window.__FLIGHT_SEARCH_REQUEST__ = "
        start = body.index(marker) + len(marker)
        end = body.index(";", start)
        return json.loads(body[start:end])

    def test_oneway_page_embeds_correct_payload(self):
        response = self.client.get("/flight/results/", {
            "trip_type": "oneway",
            "origin": "DEL",
            "destination": "GOI",
            "departure_date": self.tomorrow,
            "adults": 2,
        })

        self.assertEqual(response.status_code, 200)
        payload = self._extract_payload(response)

        self.assertEqual(payload["trip_type"], "oneway")
        self.assertEqual(payload["origin"], "DEL")
        self.assertEqual(payload["destination"], "GOI")
        self.assertEqual(payload["departure_date"], self.tomorrow)
        self.assertEqual(payload["adults"], 2)
        self.assertNotIn("segments", payload)

    def test_roundtrip_page_embeds_both_dates(self):
        response = self.client.get("/flight/results/", {
            "trip_type": "roundtrip",
            "origin": "DEL",
            "destination": "BLR",
            "departure_date": self.tomorrow,
            "return_date": self.later,
        })

        self.assertEqual(response.status_code, 200)
        payload = self._extract_payload(response)

        self.assertEqual(payload["trip_type"], "roundtrip")
        self.assertEqual(payload["departure_date"], self.tomorrow)
        self.assertEqual(payload["return_date"], self.later)

    def test_multicity_page_parses_segments_json_param(self):
        day1 = (datetime.date.today() + datetime.timedelta(days=3)).isoformat()
        day2 = (datetime.date.today() + datetime.timedelta(days=6)).isoformat()
        day3 = (datetime.date.today() + datetime.timedelta(days=9)).isoformat()

        segments = json.dumps([
            {"origin": "DEL", "destination": "BOM", "departure_date": day1},
            {"origin": "BOM", "destination": "BLR", "departure_date": day2},
            {"origin": "BLR", "destination": "DEL", "departure_date": day3},
        ])

        response = self.client.get("/flight/results/", {
            "trip_type": "multicity",
            "segments": segments,
        })

        self.assertEqual(response.status_code, 200)
        payload = self._extract_payload(response)

        self.assertEqual(payload["trip_type"], "multicity")
        self.assertEqual(len(payload["segments"]), 3)
        self.assertEqual(payload["segments"][0]["origin"], "DEL")
        self.assertEqual(payload["segments"][2]["destination"], "DEL")

    def test_invalid_segments_json_redirects_home_with_error(self):
        response = self.client.get("/flight/results/", {
            "trip_type": "multicity",
            "segments": "not-valid-json{{{",
        }, follow=False)

        self.assertEqual(response.status_code, 302)
        self.assertIn("search_error", response["Location"])

    def test_invalid_search_still_redirects_home(self):
        response = self.client.get("/flight/results/", {
            "trip_type": "oneway",
            "origin": "ZZZ",
            "destination": "GOI",
            "departure_date": self.tomorrow,
        }, follow=False)

        self.assertEqual(response.status_code, 302)
        self.assertIn("search_error", response["Location"])

    def test_page_never_contains_static_demo_flight_markers(self):
        """
        Regression guard: the old static/demo flights.html hardcoded
        specific example values (IndiGo flight 2134, ₹6,245, "42
        flights found"). None of these must appear anywhere on the
        page now that results are live-fetched.
        """
        response = self.client.get("/flight/results/", {
            "trip_type": "oneway",
            "origin": "DEL",
            "destination": "GOI",
            "departure_date": self.tomorrow,
        })

        body = response.content.decode()
        self.assertNotIn("6E 2134", body)
        self.assertNotIn("42 flights found", body)
        self.assertNotIn("₹6,245", body)

    def test_page_contains_loading_no_results_and_error_states(self):
        response = self.client.get("/flight/results/", {
            "trip_type": "oneway",
            "origin": "DEL",
            "destination": "GOI",
            "departure_date": self.tomorrow,
        })

        body = response.content.decode()
        self.assertIn('id="flight-results-loading"', body)
        self.assertIn('id="flight-results-empty"', body)
        self.assertIn('id="flight-results-error"', body)

    def test_page_never_contains_tripjack_credential(self):
        from django.conf import settings

        response = self.client.get("/flight/results/", {
            "trip_type": "oneway",
            "origin": "DEL",
            "destination": "GOI",
            "departure_date": self.tomorrow,
        })

        body = response.content.decode()
        self.assertNotIn("TRIPJACK_API_KEY", body)
        if settings.TRIPJACK_API_KEY:
            self.assertNotIn(settings.TRIPJACK_API_KEY, body)
