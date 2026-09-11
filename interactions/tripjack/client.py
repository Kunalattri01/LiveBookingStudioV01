"""
TripJack HTTP client.

Verified against a real, successful TripJack UAT request/response
(captured via Postman by the project owner) - see
docs/tripjack-integration.md for the full verification record.

Implemented flight endpoints used by the current booking flow:

    POST {base_url}/fms/v1/air-search-all
    POST {base_url}/fms/v1/review
    POST {base_url}/fms/v2/farerule
    POST {base_url}/fms/v1/seat

All use the TripJack `apikey` and JSON content type. Search request/response
mapping is verified against the supplied UAT material. Review and seat-map
methods are wired to the exact collection endpoints; live UAT execution is
still dependent on network access and account/inventory availability.

SECURITY: this module never logs or prints the API key, headers, or
request/response bodies.
"""

from django.conf import settings

from .exceptions import TripJackNotConfiguredError, TripJackRequestError

AIR_SEARCH_ALL_PATH = "/fms/v1/air-search-all"
AIR_REVIEW_PATH = "/fms/v1/review"
AIR_FARE_RULE_PATH = "/fms/v2/farerule"
AIR_SEAT_PATH = "/fms/v1/seat"


class TripJackClient:
    def __init__(self):
        self.api_key = getattr(settings, "TRIPJACK_API_KEY", "")
        self.base_url = getattr(settings, "TRIPJACK_BASE_URL", "")
        self.timeout = int(getattr(settings, "TRIPJACK_TIMEOUT_SECONDS", 20))

    def is_configured(self) -> bool:
        return bool(self.api_key and self.base_url)

    def _require_configured(self):
        if not self.is_configured():
            raise TripJackNotConfiguredError(
                "TRIPJACK_API_KEY and/or TRIPJACK_BASE_URL are not set. "
                "Configure them via environment variables before making "
                "TripJack requests."
            )

    def search_flights(self, payload: dict) -> dict:
        """
        Calls the verified TripJack air-search-all endpoint and returns
        the parsed JSON response.

        Raises TripJackRequestError (never leaking the API key or
        headers) on: missing configuration, network/timeout failure,
        non-200 HTTP response, non-JSON response, or a JSON response
        whose status.success is not true.
        """

        self._require_configured()

        import requests  # local import: only needed once this is used

        url = self.base_url.rstrip("/") + AIR_SEARCH_ALL_PATH

        headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        except requests.Timeout as exc:
            raise TripJackRequestError("TripJack request timed out.") from exc
        except requests.RequestException as exc:
            raise TripJackRequestError("TripJack request failed.") from exc

        if response.status_code != 200:
            raise TripJackRequestError(
                f"TripJack returned an unexpected HTTP status: {response.status_code}."
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise TripJackRequestError("TripJack returned a non-JSON response.") from exc

        status_block = data.get("status") if isinstance(data, dict) else None

        if not isinstance(status_block, dict) or status_block.get("success") is not True:
            raise TripJackRequestError("TripJack reported an unsuccessful search.")

        return data

    def _post_json(self, path: str, payload: dict) -> dict:
        self._require_configured()
        import requests

        url = self.base_url.rstrip("/") + path
        headers = {"apikey": self.api_key, "Content-Type": "application/json"}
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        except requests.Timeout as exc:
            raise TripJackRequestError("TripJack request timed out.") from exc
        except requests.RequestException as exc:
            raise TripJackRequestError("TripJack request failed.") from exc
        if response.status_code != 200:
            raise TripJackRequestError(
                f"TripJack returned an unexpected HTTP status: {response.status_code}."
            )
        try:
            return response.json()
        except ValueError as exc:
            raise TripJackRequestError("TripJack returned a non-JSON response.") from exc

    def review_fares(self, price_ids: list[str]) -> dict:
        if not price_ids:
            raise TripJackRequestError("At least one fare reference is required for review.")
        return self._post_json(AIR_REVIEW_PATH, {"priceIds": price_ids})

    def fare_rule(self, reference_id: str, flow_type: str = "SEARCH") -> dict:
        if not reference_id:
            raise TripJackRequestError("A fare-rule reference is required.")
        return self._post_json(
            AIR_FARE_RULE_PATH, {"id": reference_id, "flowType": flow_type}
        )

    def seat_map(self, booking_id: str) -> dict:
        if not booking_id:
            raise TripJackRequestError("A booking ID is required for seat selection.")
        return self._post_json(AIR_SEAT_PATH, {"bookingId": booking_id})
