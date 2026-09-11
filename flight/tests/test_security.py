import datetime

from django.test import TestCase


class SearchErrorNoServerSideHtmlLeakTests(TestCase):
    """
    Guards against a regression of the reflected-XSS issue found during
    Phase 2 security review: a validation error message can embed
    user-supplied text (e.g. an invalid airport code). This test only
    proves the server never echoes that raw payload back into any
    HTML page body itself. The actual toast rendering safety
    (textContent vs innerHTML) is a frontend concern verified
    separately in templates/base/public_base.html.
    """

    def test_flight_results_redirect_does_not_leak_raw_payload_in_any_page_body(self):
        tomorrow = (datetime.date.today() + datetime.timedelta(days=5)).isoformat()
        payload = "<img src=x onerror=alert(1)>"

        response = self.client.get(
            "/flight/results/",
            {
                "trip_type": "oneway",
                "origin": payload,
                "destination": "BLR",
                "departure_date": tomorrow,
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertNotIn(payload, response.get("Location", ""))

        followed = self.client.get(response["Location"])
        self.assertEqual(followed.status_code, 200)
        self.assertNotIn(payload, followed.content.decode())
