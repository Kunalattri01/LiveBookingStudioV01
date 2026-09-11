from django.test import TestCase


class TravellerPagePassportFieldTests(TestCase):
    """
    We checked the real TripJack certification logs and none of the
    captured review responses actually carry a passport-required
    flag, so we can't rely on that alone. These tests make sure our
    own fallback (checking the airports involved against our own
    master data) gets this right for the common cases.
    """

    def _set_session(self, origin=None, destination=None, segments=None):
        session = self.client.session
        session["flight_review"] = {"booking_id": "abc123"}
        search_request = {}
        if origin:
            search_request["origin"] = origin
        if destination:
            search_request["destination"] = destination
        if segments:
            search_request["segments"] = segments
        session["flight_search_request"] = search_request
        session.save()

    def test_domestic_oneway_does_not_flag_international(self):
        self._set_session(origin="DEL", destination="BOM")
        response = self.client.get("/flight/traveller/")
        self.assertContains(response, "__FLIGHT_IS_INTERNATIONAL__ = false")

    def test_international_oneway_flags_international(self):
        self._set_session(origin="DEL", destination="DXB")
        response = self.client.get("/flight/traveller/")
        self.assertContains(response, "__FLIGHT_IS_INTERNATIONAL__ = true")

    def test_multicity_with_one_international_leg_flags_international(self):
        self._set_session(segments=[
            {"origin": "DEL", "destination": "BOM"},
            {"origin": "BOM", "destination": "DXB"},
        ])
        response = self.client.get("/flight/traveller/")
        self.assertContains(response, "__FLIGHT_IS_INTERNATIONAL__ = true")

    def test_multicity_fully_domestic_does_not_flag_international(self):
        self._set_session(segments=[
            {"origin": "DEL", "destination": "BOM"},
            {"origin": "BOM", "destination": "BLR"},
        ])
        response = self.client.get("/flight/traveller/")
        self.assertContains(response, "__FLIGHT_IS_INTERNATIONAL__ = false")
