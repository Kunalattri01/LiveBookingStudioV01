from typing import Any, Dict, List

from ..services.dto import (
    CancellationInfo,
    CancellationPenalty,
    CommercialInfo,
    ComplianceInfo,
    HotelOption,
    NormalizedHotel,
    NormalizedHotelDetail,
    NormalizedHotelReview,
    PricingInfo,
    RoomInfo,
)
from .base import HotelNormalizer


class TripJackHotelNormalizationError(Exception):
    """Raised when a TripJack Hotel response is missing an expected key/shape."""


class TripJackHotelNormalizer(HotelNormalizer):
    """
    Converts raw TripJack Hotel API v3 JSON into our supplier-neutral
    DTOs (hotel/services/dto.py). Every field is read with `.get()`
    and no invented default - see the DTO docstrings for exact field
    provenance (verified against the TripJack Hotel API v3 partner
    reference supplied by the project owner).
    """

    def normalize_listing(self, raw_response: Dict[str, Any]) -> dict:
        if not isinstance(raw_response, dict) or "hotels" not in raw_response:
            raise TripJackHotelNormalizationError(
                "TripJack Hotel listing response is missing the expected 'hotels' key."
            )

        hotels = [self._normalize_hotel(entry) for entry in raw_response.get("hotels") or []]

        return {
            "hotels": hotels,
            "correlation_id": raw_response.get("correlationId"),
            "currency": raw_response.get("currency"),
            "nationality": raw_response.get("nationality"),
            "total_results": raw_response.get("totalResults"),
        }

    def normalize_detail(self, raw_response: Dict[str, Any]) -> NormalizedHotelDetail:
        if not isinstance(raw_response, dict) or "options" not in raw_response:
            raise TripJackHotelNormalizationError(
                "TripJack Hotel pricing response is missing the expected 'options' key."
            )

        options = [self._normalize_option(entry) for entry in raw_response.get("options") or []]

        return NormalizedHotelDetail(
            # See normalize_listing: live responses use "hotelId", not the
            # documented "tjHotelId". Accept either.
            tj_hotel_id=raw_response.get("tjHotelId") or raw_response.get("hotelId"),
            hotel_name=raw_response.get("hotelName"),
            nationality=raw_response.get("nationality"),
            options=options,
            review_hash=raw_response.get("reviewHash"),
            correlation_id=raw_response.get("correlationId"),
        )

    def normalize_review(self, raw_response: Dict[str, Any]) -> NormalizedHotelReview:
        if not isinstance(raw_response, dict) or "option" not in raw_response:
            raise TripJackHotelNormalizationError(
                "TripJack Hotel review response is missing the expected 'option' key."
            )

        raw_option = raw_response.get("option") or {}
        onhold_raw = raw_response.get("onholdAllowed")

        return NormalizedHotelReview(
            correlation_id=raw_response.get("correlationId"),
            tj_hotel_id=raw_response.get("tjHotelId") or raw_response.get("hotelId"),
            hotel_name=raw_response.get("hotelName"),
            booking_id=raw_response.get("bookingId"),
            option=self._normalize_option(raw_option),
            deadline_datetime=raw_option.get("deadlineDateTime"),
            onhold_allowed=self._as_bool(onhold_raw),
        )

    def _normalize_hotel(self, entry: Dict[str, Any]) -> NormalizedHotel:
        return NormalizedHotel(
            # The API reference documents this field as "tjHotelId", but the
            # live Listing response actually returns it as "hotelId" -
            # verified against a real TripJack sandbox response. Accept
            # either so normalization doesn't silently drop the ID.
            tj_hotel_id=entry.get("tjHotelId") or entry.get("hotelId"),
            name=entry.get("name"),
            options=[self._normalize_option(o) for o in entry.get("options") or []],
        )

    def _normalize_option(self, entry: Dict[str, Any]) -> HotelOption:
        return HotelOption(
            option_id=entry.get("optionId"),
            option_type=entry.get("optionType"),
            room_info=[self._normalize_room_info(r) for r in entry.get("roomInfo") or []],
            inclusions=list(entry.get("inclusions") or []),
            meal_basis=entry.get("mealBasis"),
            booking_notes=entry.get("bookingNotes"),
            pricing=self._normalize_pricing(entry.get("pricing") or {}),
            commercial=self._normalize_commercial(entry.get("commercial") or {}),
            compliance=self._normalize_compliance(entry.get("compliance") or {}),
            cancellation=self._normalize_cancellation(entry.get("cancellation") or {}),
        )

    @staticmethod
    def _normalize_room_info(entry: Dict[str, Any]) -> RoomInfo:
        return RoomInfo(
            id=entry.get("id"),
            name=entry.get("name"),
            adults=entry.get("adults"),
            children=entry.get("children"),
        )

    @staticmethod
    def _normalize_pricing(entry: Dict[str, Any]) -> PricingInfo:
        return PricingInfo(
            total_price=entry.get("totalPrice"),
            base_price=entry.get("basePrice"),
            discount=entry.get("discount"),
            taxes=entry.get("taxes"),
            mf=entry.get("mf"),
            mft=entry.get("mft"),
            currency=entry.get("currency"),
            strikethrough=entry.get("strikethrough"),
        )

    @staticmethod
    def _normalize_commercial(entry: Dict[str, Any]) -> CommercialInfo:
        return CommercialInfo(type=entry.get("type"), commission=entry.get("commission"))

    @staticmethod
    def _normalize_compliance(entry: Dict[str, Any]) -> ComplianceInfo:
        return ComplianceInfo(
            gst_type=entry.get("gstType"),
            pan_required=entry.get("panRequired"),
            passport_required=entry.get("passportRequired"),
        )

    def _normalize_cancellation(self, entry: Dict[str, Any]) -> CancellationInfo:
        penalties: List[CancellationPenalty] = [
            CancellationPenalty(
                from_date=p.get("from"), to_date=p.get("to"), amount=p.get("amount")
            )
            for p in entry.get("penalties") or []
        ]
        return CancellationInfo(is_refundable=entry.get("isRefundable"), penalties=penalties)

    @staticmethod
    def _as_bool(value: Any):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ("true", "1", "yes")
        return None
