"""
MOCK / DEMO PROVIDER - not live data, but not invented either.

Every field below is a frozen copy of a real response captured from a
live TripJack UAT session on 2026-09-04 for tj_hotel_id=100000078396
(Priya Living Flower Valley, Gurugram) - see the probe scripts used
during development for the original captures. Used only when
HOTEL_PROVIDER is explicitly set to "mock", which is NEVER the
default and is not reachable by any unset/unknown/typo'd value (see
providers/manager.py and providers/unconfigured_provider.py) - it
exists purely so the search -> listing -> detail -> review -> book ->
confirmation funnel can be demonstrated end-to-end while TripJack's
UAT sandbox has no stable live inventory to point at.

This must never be the default for real web/mobile traffic.
"""

import uuid

from ..services.booking_dto import NormalizedBookingDetails, NormalizedBookResult
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
from .base import HotelProvider
from .booking_base import HotelBookingProvider

MOCK_HOTEL_ID = "100000078396"
MOCK_HOTEL_NAME = "Priya Living Flower Valley"

_CANCELLATION = CancellationInfo(
    is_refundable=True,
    penalties=[
        CancellationPenalty(from_date="2026-09-04T11:34:00", to_date="2026-09-09T23:59:59", amount=0.0),
        CancellationPenalty(from_date="2026-09-09T23:59:59", to_date="2026-09-12T00:00:00", amount=6375.34),
    ],
)

_MOCK_OPTIONS = [
    HotelOption(
        option_id="mock-3ddbdd1e-d430-4ebc-8d5b-1cca274b0eed",
        option_type="SRSM",
        room_info=[RoomInfo(id="10025045233", name="Deluxe Single Room", adults=1, children=0)],
        inclusions=[],
        meal_basis="Breakfast",
        booking_notes=None,
        pricing=PricingInfo(total_price=6398.94, base_price=6375.34, discount=0.0, taxes=0.0, mf=20.0, mft=3.6, currency="INR"),
        commercial=CommercialInfo(type="NET", commission=0.0),
        compliance=ComplianceInfo(gst_type="NA", pan_required=True, passport_required=False),
        cancellation=_CANCELLATION,
    ),
    HotelOption(
        option_id="mock-fd95d28d-dc41-41ac-849b-7d849fce6c05",
        option_type="SRSM",
        room_info=[RoomInfo(id="10025045234", name="Premium Studio", adults=1, children=0)],
        inclusions=[],
        meal_basis="Breakfast",
        booking_notes=None,
        pricing=PricingInfo(total_price=7421.94, base_price=7398.34, discount=0.0, taxes=0.0, mf=20.0, mft=3.6, currency="INR"),
        commercial=CommercialInfo(type="NET", commission=0.0),
        compliance=ComplianceInfo(gst_type="NA", pan_required=True, passport_required=False),
        cancellation=_CANCELLATION,
    ),
    HotelOption(
        option_id="mock-84f97521-5614-413b-bad6-ed3e16c21c6f",
        option_type="SRSM",
        room_info=[RoomInfo(id="10025045232", name="Deluxe Double Room", adults=1, children=0)],
        inclusions=[],
        meal_basis="Breakfast",
        booking_notes=None,
        pricing=PricingInfo(total_price=10725.75, base_price=10702.15, discount=0.0, taxes=0.0, mf=20.0, mft=3.6, currency="INR"),
        commercial=CommercialInfo(type="NET", commission=0.0),
        compliance=ComplianceInfo(gst_type="NA", pan_required=True, passport_required=False),
        cancellation=_CANCELLATION,
    ),
]


class MockHotelProvider(HotelProvider):
    """Search-side mock: always returns the frozen Priya Living Flower Valley snapshot."""

    def search(self, search_request) -> dict:
        return {
            "hotels": [NormalizedHotel(tj_hotel_id=MOCK_HOTEL_ID, name=MOCK_HOTEL_NAME, options=[_MOCK_OPTIONS[0]])],
            "correlation_id": search_request.correlation_id,
            "currency": "INR",
            "nationality": search_request.nationality,
            "total_results": 1,
        }

    def detail(self, detail_request) -> NormalizedHotelDetail:
        return NormalizedHotelDetail(
            tj_hotel_id=MOCK_HOTEL_ID,
            hotel_name=MOCK_HOTEL_NAME,
            nationality=detail_request.nationality,
            options=_MOCK_OPTIONS,
            review_hash="MOCK-REVIEW-HASH",
            correlation_id=detail_request.correlation_id,
        )

    def review(self, review_request) -> NormalizedHotelReview:
        option = next((o for o in _MOCK_OPTIONS if o.option_id == review_request.option_id), _MOCK_OPTIONS[0])
        return NormalizedHotelReview(
            correlation_id=review_request.correlation_id,
            tj_hotel_id=MOCK_HOTEL_ID,
            hotel_name=MOCK_HOTEL_NAME,
            booking_id="MOCK-" + uuid.uuid4().hex[:12].upper(),
            option=option,
            deadline_datetime="2026-09-09T23:59:59",
            onhold_allowed=True,
        )


class MockHotelBookingProvider(HotelBookingProvider):
    """Booking-side mock: always accepts the booking and reports it confirmed."""

    def book(self, book_request) -> NormalizedBookResult:
        return NormalizedBookResult(booking_id="MOCK-TJ-" + uuid.uuid4().hex[:10].upper(), accepted=True)

    def booking_details(self, booking_id: str) -> NormalizedBookingDetails:
        return NormalizedBookingDetails(
            booking_id=booking_id,
            status="CONFIRMED",
            amount=6398.94,
            currency="INR",
            hotel_name=MOCK_HOTEL_NAME,
            confirmation_number=booking_id,
            created_on="2026-09-04T17:11:41.823",
            raw={"mock": True, "note": "Static demo data - see hotel/providers/mock_provider.py"},
        )
