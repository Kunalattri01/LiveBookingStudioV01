from typing import List

from ..normalizers.tripjack import TripJackHotelNormalizer
from ..services.dto import HotelDetailRequest, HotelReviewRequest, HotelSearchRequest, NormalizedHotelDetail, NormalizedHotelReview, RoomRequest
from .base import HotelProvider
from .exceptions import ProviderUpstreamError
from .tripjack_client import TripJackHotelClient
from .tripjack_exceptions import TripJackHotelError


class TripJackHotelAdapter(HotelProvider):
    """
    Adapter for TripJack Hotel API v3 inventory (Listing / Pricing /
    Review). Request and response shapes are verified against the
    TripJack Hotel API v3 partner reference supplied by the project
    owner, including its sample requests/responses.
    """

    def __init__(self):
        self.client = TripJackHotelClient()
        self.normalizer = TripJackHotelNormalizer()

    def search(self, search_request: HotelSearchRequest) -> dict:
        payload = self._build_listing_payload(search_request)
        return self._call(self.client.listing, payload, self.normalizer.normalize_listing)

    def detail(self, detail_request: HotelDetailRequest) -> NormalizedHotelDetail:
        payload = self._build_pricing_payload(detail_request)
        normalized = self._call(self.client.pricing, payload, self.normalizer.normalize_detail)
        self._attach_room_static_content(normalized, detail_request.hid)
        return normalized

    def _attach_room_static_content(self, detail: NormalizedHotelDetail, hid: str) -> None:
        """
        Best-effort enrichment: merges room images/description/bed
        layout/area/amenities from fetch-hotel-content (static content,
        matched by roomInfo.id) onto the already-normalized Pricing
        result. Pricing/availability themselves are never touched -
        this only ever adds catalogue metadata TripJack's Pricing
        response doesn't carry. Silently skipped (never fails the
        detail request) if the static-content call errors - it's
        display polish, not required for booking.
        """
        try:
            raw = self.client.hotel_content([hid])
        except TripJackHotelError:
            return

        hotels = raw.get("hotels") or []
        if not hotels:
            return

        rooms_by_id = {}
        for room in (hotels[0].get("rooms") or {}).values():
            room_id = room.get("id")
            if room_id:
                rooms_by_id[str(room_id)] = room

        for option in detail.options:
            for room_info in option.room_info:
                static_room = rooms_by_id.get(str(room_info.id))
                if not static_room:
                    continue

                room_info.image_url = self._pick_room_image(static_room.get("images") or [])
                room_info.description = (static_room.get("descriptions") or {}).get("overview")

                bed_config = static_room.get("bed_config") or {}
                room_info.bed_summary = bed_config.get("description")

                area = static_room.get("area") or {}
                room_info.area_sqft = area.get("square_feet")

                amenities_map = static_room.get("amenities") or {}
                room_info.amenities = [
                    a.get("name") for a in amenities_map.values() if a.get("name")
                ]

                occupancy = (static_room.get("occupancy") or {}).get("max_allowed") or {}
                room_info.max_occupancy_total = occupancy.get("total")

    @staticmethod
    def _pick_room_image(images):
        """
        Room-level images use `hero_image` (not `is_hero_image` - that
        spelling is hotel-level-only in fetch-hotel-content's response).
        """
        if not images:
            return None

        hero = next((img for img in images if img.get("hero_image")), images[0])
        links = hero.get("links") or {}
        if not links:
            return None

        if "original" in links:
            return (links["original"] or {}).get("href")

        def _px_size(key):
            digits = "".join(ch for ch in key if ch.isdigit())
            return int(digits) if digits else -1

        best_key = max(links, key=_px_size)
        return (links[best_key] or {}).get("href")

    def review(self, review_request: HotelReviewRequest) -> NormalizedHotelReview:
        payload = {
            "correlationId": review_request.correlation_id,
            "optionId": review_request.option_id,
            "reviewHash": review_request.review_hash,
            "hid": review_request.hid,
        }
        return self._call(self.client.review, payload, self.normalizer.normalize_review)

    def _call(self, client_method, payload: dict, normalize):
        try:
            raw_response = client_method(payload)
        except TripJackHotelError as exc:
            raise ProviderUpstreamError(str(exc)) from exc

        try:
            return normalize(raw_response)
        except Exception as exc:  # noqa: BLE001 - normalization failure is an upstream-data problem
            raise ProviderUpstreamError(
                "TripJack Hotel returned a response that could not be normalized."
            ) from exc

    @staticmethod
    def _build_rooms(rooms: List[RoomRequest]) -> List[dict]:
        payload_rooms = []
        for room in rooms:
            entry = {"adults": room.adults}
            if room.children:
                entry["children"] = room.children
                entry["childAge"] = list(room.child_ages)
            payload_rooms.append(entry)
        return payload_rooms

    def _build_listing_payload(self, search_request: HotelSearchRequest) -> dict:
        return {
            "checkIn": search_request.check_in.isoformat(),
            "checkOut": search_request.check_out.isoformat(),
            "rooms": self._build_rooms(search_request.rooms),
            "currency": search_request.currency,
            "correlationId": search_request.correlation_id,
            "nationality": search_request.nationality,
            "hids": [int(h) if str(h).isdigit() else h for h in search_request.hids],
        }

    def _build_pricing_payload(self, detail_request: HotelDetailRequest) -> dict:
        return {
            "correlationId": detail_request.correlation_id,
            "hid": detail_request.hid,
            "checkIn": detail_request.check_in.isoformat(),
            "checkOut": detail_request.check_out.isoformat(),
            "rooms": self._build_rooms(detail_request.rooms),
            "currency": detail_request.currency,
            "nationality": detail_request.nationality,
        }
