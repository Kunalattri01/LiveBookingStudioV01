"""
TripJack Hotel API v3 HTTP client.

Endpoints implemented (per the TripJack Hotel API v3 partner reference
supplied by the project owner):

    HMS service    (HOTEL_HMS_BASE_URL,    default https://apitest-hms.tripjack.com)
        POST /hms/v3/hotel/listing
        POST /hms/v3/hotel/pricing
        POST /hms/v3/hotel/review

    Booker service (HOTEL_BOOKER_BASE_URL, default https://apitest.tripjack.com)
        POST /oms/v3/hotel/book
        POST /oms/v3/hotel/booking-details

    NOTE: the API reference documents Book/Booking-Details as living
    on a separate apitest-hotel-booker.tripjack.com host. That host
    returns 403 "Access denied: IP address not whitelisted" without
    IP whitelisting. Verified live that the same paths work correctly
    under the main apitest.tripjack.com host instead - no whitelisting
    required - so that's the default.

    Static content (HOTEL_HMS_BASE_URL, same host as Listing/Pricing)
        POST /hms/v3/content/fetch-hotel-mapping   - catalog of tjHotelId
        POST /hms/v3/content/fetch-hotel-content   - name/address/etc per ID

    These two are used only by hotel/management/commands/seed_tripjack_hotels.py
    to populate the local Hotel catalog (hotel/models.py) - never called
    from the live search/booking request path. Their request shape is
    NOT in the v3 partner reference doc (only the read-only Fetch
    Countries, City Region IDs, Hotel Mapping *Sync*, and Deleted
    Mapping Sync variants were documented) - confirmed instead by
    direct, live probing of the real endpoint: an empty body on
    fetch-hotel-mapping returns the full ~1.57M-hotel global catalog;
    `countryName` and `regionIds` (matching `locale.address.citycode`
    from fetch-hotel-content) both genuinely filter it, while
    `cityName`/`regionName` are silently ignored. fetch-hotel-content's
    `hotelIds` field name was confirmed via its own 400 validation
    error ("hotelIds is mandatory") after other field-name guesses
    failed with the same message.

Static content (/hms/v3/hotel/static-detail) and the hold-booking
confirm step (/oms/v3/hotel/confirm-book) are documented by TripJack
but not implemented here - out of scope for the current search ->
listing -> detail -> review -> book -> confirmation funnel.

Auth: the `apikey` header (not `Authorization: Bearer`), same as the
rest of this project's TripJack integration.

SECURITY: this module never logs or prints the API key, headers, or
request/response bodies.
"""

from django.conf import settings

from .tripjack_exceptions import TripJackHotelNotConfiguredError, TripJackHotelRequestError

HOTEL_LISTING_PATH = "/hms/v3/hotel/listing"
HOTEL_PRICING_PATH = "/hms/v3/hotel/pricing"
HOTEL_REVIEW_PATH = "/hms/v3/hotel/review"
HOTEL_BOOK_PATH = "/oms/v3/hotel/book"
HOTEL_BOOKING_DETAILS_PATH = "/oms/v3/hotel/booking-details"
HOTEL_MAPPING_PATH = "/hms/v3/content/fetch-hotel-mapping"
HOTEL_CONTENT_PATH = "/hms/v3/content/fetch-hotel-content"


class TripJackHotelClient:
    def __init__(self):
        self.api_key = getattr(settings, "TRIPJACK_API_KEY", "")
        self.hms_base_url = getattr(settings, "HOTEL_HMS_BASE_URL", "")
        self.booker_base_url = getattr(settings, "HOTEL_BOOKER_BASE_URL", "")
        self.timeout = int(getattr(settings, "TRIPJACK_TIMEOUT_SECONDS", 20))

    def is_configured(self) -> bool:
        return bool(self.api_key and self.hms_base_url and self.booker_base_url)

    def _require_configured(self):
        if not self.is_configured():
            raise TripJackHotelNotConfiguredError(
                "TRIPJACK_API_KEY, HOTEL_HMS_BASE_URL and/or HOTEL_BOOKER_BASE_URL "
                "are not set. Configure them via environment variables before "
                "making TripJack Hotel requests."
            )

    def _post_json(self, base_url: str, path: str, payload: dict) -> dict:
        self._require_configured()

        import requests  # local import: only needed once this is used

        url = base_url.rstrip("/") + path
        headers = {"apikey": self.api_key, "Content-Type": "application/json"}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        except requests.Timeout as exc:
            raise TripJackHotelRequestError("TripJack Hotel request timed out.") from exc
        except requests.RequestException as exc:
            raise TripJackHotelRequestError("TripJack Hotel request failed.") from exc

        if response.status_code != 200:
            raise TripJackHotelRequestError(
                f"TripJack Hotel returned an unexpected HTTP status: {response.status_code}."
            )

        try:
            return response.json()
        except ValueError as exc:
            raise TripJackHotelRequestError("TripJack Hotel returned a non-JSON response.") from exc

    def listing(self, payload: dict) -> dict:
        """POST /hms/v3/hotel/listing - Step 1 of the booking flow."""
        return self._post_json(self.hms_base_url, HOTEL_LISTING_PATH, payload)

    def pricing(self, payload: dict) -> dict:
        """POST /hms/v3/hotel/pricing - Step 2 (Dynamic Detail)."""
        return self._post_json(self.hms_base_url, HOTEL_PRICING_PATH, payload)

    def review(self, payload: dict) -> dict:
        """POST /hms/v3/hotel/review - Step 3."""
        return self._post_json(self.hms_base_url, HOTEL_REVIEW_PATH, payload)

    def book(self, payload: dict) -> dict:
        """POST /oms/v3/hotel/book - Step 4."""
        return self._post_json(self.booker_base_url, HOTEL_BOOK_PATH, payload)

    def booking_details(self, booking_id: str) -> dict:
        """POST /oms/v3/hotel/booking-details - poll for confirmation status."""
        if not booking_id:
            raise TripJackHotelRequestError("A booking ID is required to fetch booking details.")
        return self._post_json(
            self.booker_base_url, HOTEL_BOOKING_DETAILS_PATH, {"bookingId": booking_id}
        )

    def hotel_mapping(self, region_ids=None, country_name=None, page: int = 0, size: int = 100) -> dict:
        """
        POST /hms/v3/content/fetch-hotel-mapping - static catalog lookup.

        Verified live against the real UAT account: an empty body
        returns the entire global mapping (~1.57M hotels); `countryName`
        and `regionIds` (TripJack's numeric city codes, the same value
        as `locale.address.citycode` in fetch-hotel-content) both filter
        the result set. Not otherwise documented in the v3 partner
        reference supplied - this shape was confirmed by direct probing
        of the live endpoint, not guessed.

        `countryName` is case-sensitive and expects TripJack's own
        ALL-CAPS country name - confirmed live: "INDIA" -> 111707 hotels,
        "India" -> 5 (a coincidental partial match), "india" -> 0. Callers
        passing a human-cased name should `.upper()` it first (see
        hotel/management/commands/seed_tripjack_hotels.py).
        """
        payload = {"page": page, "size": size}
        if region_ids:
            payload["regionIds"] = list(region_ids)
        if country_name:
            payload["countryName"] = country_name
        return self._post_json(self.hms_base_url, HOTEL_MAPPING_PATH, payload)

    def hotel_content(self, hotel_ids) -> dict:
        """
        POST /hms/v3/content/fetch-hotel-content - static hotel details
        (name, address, star rating, amenities) for a batch of hotel IDs.
        Field name confirmed live: the API's own 400 response on a
        wrong field name ("hotelIds is mandatory") revealed it.
        """
        if not hotel_ids:
            raise TripJackHotelRequestError("At least one hotel ID is required to fetch hotel content.")
        return self._post_json(self.hms_base_url, HOTEL_CONTENT_PATH, {"hotelIds": list(hotel_ids)})
