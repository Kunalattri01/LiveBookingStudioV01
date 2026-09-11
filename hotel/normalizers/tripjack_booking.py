from typing import Any, Dict, Optional

from ..services.booking_dto import NormalizedBookingDetails, NormalizedBookResult
from .base import HotelBookingNormalizer


class TripJackHotelBookingNormalizationError(Exception):
    """Raised when a TripJack Hotel booking-side response is missing an expected key/shape."""


class TripJackHotelBookingNormalizer(HotelBookingNormalizer):
    """Normalizes the Book and Booking Details responses (hotel/providers/tripjack_client.py)."""

    def normalize_book(self, raw_response: Dict[str, Any]) -> NormalizedBookResult:
        if not isinstance(raw_response, dict):
            raise TripJackHotelBookingNormalizationError("TripJack Hotel book response was not a JSON object.")

        status_block = raw_response.get("status") or {}

        return NormalizedBookResult(
            booking_id=raw_response.get("bookingId"),
            accepted=bool(status_block.get("success")),
        )

    def normalize_booking_details(self, raw_response: Dict[str, Any]) -> NormalizedBookingDetails:
        if not isinstance(raw_response, dict) or "order" not in raw_response:
            raise TripJackHotelBookingNormalizationError(
                "TripJack Hotel booking-details response is missing the expected 'order' key."
            )

        order = raw_response.get("order") or {}
        item_infos = raw_response.get("itemInfos") or {}
        hotel_item = item_infos.get("HOTEL") or {}
        h_info = hotel_item.get("hInfo") or {}
        options = h_info.get("ops") or []
        currency = options[0].get("sc") if options and isinstance(options[0], dict) else None

        return NormalizedBookingDetails(
            booking_id=order.get("bookingId"),
            status=order.get("status"),
            amount=self._as_float(order.get("amount")),
            currency=currency,
            hotel_name=h_info.get("name"),
            confirmation_number=raw_response.get("hotelConfirmationNumber"),
            created_on=order.get("createdOn"),
            raw=raw_response,
        )

    @staticmethod
    def _as_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
