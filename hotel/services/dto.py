from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional

VALID_TITLES = ("Mr", "Mrs", "Ms", "Miss", "Master")
VALID_PASSENGER_TYPES = ("ADULT", "CHILD")


@dataclass
class RoomRequest:
    """One room's occupancy, as sent in `rooms[]` on Listing/Pricing."""

    adults: int
    children: int = 0
    child_ages: List[int] = field(default_factory=list)


@dataclass
class HotelSearchRequest:
    """
    Stable internal representation of a hotel search, independent of
    the TripJack request shape and of how the request arrived (web
    form or JSON API).

    `hids` is what TripJack's v3 Listing API actually requires (it
    dropped `cityCode`); it is resolved server-side from `destination`
    via the local hotel.models.Hotel master table by
    hotel.services.validators.
    """

    destination: str
    check_in: date
    check_out: date
    rooms: List[RoomRequest]
    hids: List[str] = field(default_factory=list)
    currency: str = "INR"
    nationality: str = "106"
    correlation_id: Optional[str] = None


@dataclass
class HotelDetailRequest:
    """Internal representation of a Dynamic Detail (Pricing) request."""

    hid: str
    check_in: date
    check_out: date
    rooms: List[RoomRequest]
    correlation_id: str
    currency: str = "INR"
    nationality: str = "106"


@dataclass
class HotelReviewRequest:
    """Internal representation of a Review request."""

    correlation_id: str
    option_id: str
    review_hash: str
    hid: str


@dataclass
class PricingInfo:
    """
    Field provenance (TripJack Hotel API v3 `pricing` object, shared
    across Listing/Pricing/Review option objects):
        total_price   <- pricing.totalPrice
        base_price    <- pricing.basePrice
        discount      <- pricing.discount
        taxes         <- pricing.taxes
        mf            <- pricing.mf   (Management Fee)
        mft           <- pricing.mft  (Management Fee Tax)
        currency      <- pricing.currency
        strikethrough <- pricing.strikethrough (only present for commissionable rate plans)
    """

    total_price: Optional[float] = None
    base_price: Optional[float] = None
    discount: Optional[float] = None
    taxes: Optional[float] = None
    mf: Optional[float] = None
    mft: Optional[float] = None
    currency: Optional[str] = None
    strikethrough: Optional[float] = None


@dataclass
class CommercialInfo:
    """commercial.type <- NET | COMMISSIONABLE | EXTRANET; commercial.commission <- commercial.commission"""

    type: Optional[str] = None
    commission: Optional[float] = None


@dataclass
class ComplianceInfo:
    """compliance.{gstType,panRequired,passportRequired}"""

    gst_type: Optional[str] = None
    pan_required: Optional[bool] = None
    passport_required: Optional[bool] = None


@dataclass
class CancellationPenalty:
    """One slab of cancellation.penalties[]: {from, to, amount}."""

    from_date: Optional[str] = None
    to_date: Optional[str] = None
    amount: Optional[float] = None


@dataclass
class CancellationInfo:
    """cancellation.{isRefundable,penalties[]}"""

    is_refundable: Optional[bool] = None
    penalties: List[CancellationPenalty] = field(default_factory=list)


@dataclass
class RoomInfo:
    """
    One entry of options[].roomInfo[]: {id, name, adults, children} from
    the Pricing (Detail) response, PLUS static room catalogue fields
    attached afterwards by TripJackHotelAdapter from the separate
    fetch-hotel-content static-content endpoint (matched by room id).
    Per TripJack's own guidance, static content is display-only
    catalogue metadata - pricing/availability/room selection always
    come from the dynamic Pricing response, never from these fields.
    None on any field the static lookup didn't find (e.g. mock
    provider, or a room id with no static match).
    """

    id: Optional[str] = None
    name: Optional[str] = None
    adults: Optional[int] = None
    children: Optional[int] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    bed_summary: Optional[str] = None
    area_sqft: Optional[float] = None
    amenities: List[str] = field(default_factory=list)
    max_occupancy_total: Optional[int] = None


@dataclass
class HotelOption:
    """
    One bookable combination of room type / meal basis / rate plan.
    Same shape reused across Listing, Pricing (Dynamic Detail) and
    Review responses (per the TripJack v3 reference).

    Field provenance:
        option_id       <- optionId
        option_type     <- optionType (SRSM/SRCM/CRSM/CRCM)
        room_info       <- roomInfo[]
        inclusions      <- inclusions[]
        meal_basis      <- mealBasis
        booking_notes   <- bookingNotes (Pricing/Review only; absent in Listing)
        pricing         <- pricing
        commercial      <- commercial
        compliance      <- compliance
        cancellation    <- cancellation
    """

    option_id: Optional[str] = None
    option_type: Optional[str] = None
    room_info: List[RoomInfo] = field(default_factory=list)
    inclusions: List[str] = field(default_factory=list)
    meal_basis: Optional[str] = None
    booking_notes: Optional[str] = None
    pricing: Optional[PricingInfo] = None
    commercial: Optional[CommercialInfo] = None
    compliance: Optional[ComplianceInfo] = None
    cancellation: Optional[CancellationInfo] = None


@dataclass
class NormalizedHotel:
    """
    One hotel result from the Listing response.
        tj_hotel_id <- hotels[].tjHotelId
        name        <- hotels[].name
        options     <- hotels[].options[]
        image_url   <- not part of the Listing response (TripJack's
                        Listing/Pricing calls never return images) -
                        attached afterwards by HotelService from the
                        local Hotel catalog (hotel/models.py), which is
                        populated from TripJack's own static-content
                        endpoints. None when the hotel isn't in the
                        local catalog or has no image on file.
    """

    tj_hotel_id: Optional[str] = None
    name: Optional[str] = None
    options: List[HotelOption] = field(default_factory=list)
    image_url: Optional[str] = None
    star_rating: Optional[int] = None


@dataclass
class HotelSearchResult:
    """Outcome of a hotel listing search - never both data and an error, never fake data on failure."""

    success: bool
    hotels: List[NormalizedHotel] = field(default_factory=list)
    correlation_id: Optional[str] = None
    currency: Optional[str] = None
    nationality: Optional[str] = None
    total_results: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class NormalizedHotelDetail:
    """
    Outcome of the Dynamic Detail (Pricing) call.
        tj_hotel_id <- tjHotelId
        hotel_name  <- hotelName
        nationality <- nationality
        options     <- options[]
        review_hash <- reviewHash (required by the Review API)
        image_url   <- not part of the Pricing response; attached
                        afterwards by HotelService from the local
                        Hotel catalog, same as NormalizedHotel.image_url.
    """

    tj_hotel_id: Optional[str] = None
    hotel_name: Optional[str] = None
    nationality: Optional[str] = None
    options: List[HotelOption] = field(default_factory=list)
    review_hash: Optional[str] = None
    correlation_id: Optional[str] = None
    image_url: Optional[str] = None
    star_rating: Optional[int] = None


@dataclass
class HotelDetailResult:
    success: bool
    detail: Optional[NormalizedHotelDetail] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class NormalizedHotelReview:
    """
    Outcome of the Review call.
        correlation_id  <- correlationId
        tj_hotel_id     <- tjHotelId
        hotel_name      <- hotelName
        booking_id      <- bookingId (required by the Book API)
        option          <- option (confirmed HotelOption; also carries deadlineDateTime, not modelled separately)
        onhold_allowed  <- onholdAllowed (string "true"/"false" in the sample response)
    """

    correlation_id: Optional[str] = None
    tj_hotel_id: Optional[str] = None
    hotel_name: Optional[str] = None
    booking_id: Optional[str] = None
    option: Optional[HotelOption] = None
    deadline_datetime: Optional[str] = None
    onhold_allowed: Optional[bool] = None


@dataclass
class HotelReviewResult:
    success: bool
    review: Optional[NormalizedHotelReview] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
