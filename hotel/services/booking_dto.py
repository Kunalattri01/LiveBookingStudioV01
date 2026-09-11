from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TravellerInfo:
    """
    One guest, per travellerInfo[]: {ti, pt, fN, lN, pan?, pNum?}.
    `pan` is required when the reviewed option's compliance.pan_required
    is true; `passport_number` when compliance.passport_required is true.
    """

    title: str
    passenger_type: str
    first_name: str
    last_name: str
    pan: Optional[str] = None
    passport_number: Optional[str] = None


@dataclass
class RoomTravellerGroup:
    """One entry of roomTravellerInfo[] - the guests staying in one room."""

    travellers: List[TravellerInfo] = field(default_factory=list)


@dataclass
class DeliveryInfo:
    """deliveryInfo: {emails[], contacts[], code[]} - one dialing code per contact number."""

    emails: List[str] = field(default_factory=list)
    contacts: List[str] = field(default_factory=list)
    codes: List[str] = field(default_factory=list)


@dataclass
class GstInfo:
    """gstInfo: {gstNumber, registeredName} - only sent when compliance.gst_type requires it."""

    gst_number: Optional[str] = None
    registered_name: Optional[str] = None


@dataclass
class HotelBookRequest:
    """
    Internal representation of a Book request.

    `amount` present -> Instant Booking (paymentInfos included).
    `amount` None     -> Hold Booking (paymentInfos omitted); the hold
    must be confirmed separately before its deadline - confirm-book is
    not implemented by this integration yet, so hold bookings are
    accepted by the API but cannot currently be confirmed through it.
    """

    booking_id: str
    room_traveller_info: List[RoomTravellerGroup]
    delivery_info: DeliveryInfo
    gst_info: Optional[GstInfo] = None
    amount: Optional[float] = None


@dataclass
class NormalizedBookResult:
    """
    Outcome of the Book call.
        booking_id <- bookingId (TripJack's own booking/order id, distinct from the Review bookingId)
        accepted   <- status.success
    """

    booking_id: Optional[str] = None
    accepted: bool = False


@dataclass
class HotelBookResult:
    success: bool
    booking_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class NormalizedBookingDetails:
    """
    Outcome of the Booking Details call.

    Field provenance:
        booking_id           <- order.bookingId
        status                <- order.status (e.g. ON_HOLD, CONFIRMED, FAILED)
        amount                <- order.amount
        currency              <- itemInfos.HOTEL.ops[].sc, when present
        hotel_name            <- itemInfos.HOTEL.hInfo.name
        confirmation_number   <- hotelConfirmationNumber
        created_on            <- order.createdOn

    The response nests a large, loosely-documented amount of detail
    under itemInfos (room/rate/traveller/cancellation breakdown) -
    that block is kept as-is in `raw` rather than modelled field by
    field, since only the top-level status is needed to drive the
    confirmation page and its poll loop.
    """

    booking_id: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    hotel_name: Optional[str] = None
    confirmation_number: Optional[str] = None
    created_on: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HotelBookingDetailsResult:
    success: bool
    details: Optional[NormalizedBookingDetails] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
