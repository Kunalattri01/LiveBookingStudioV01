from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class NormalizedReview:
    """Supplier-neutral fare review/revalidation result."""

    booking_id: Optional[str] = None
    total_fare: Optional[float] = None
    passport_required: Optional[bool] = None
    seats_available: Optional[int] = None
    raw_status: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedSeat:
    """A supplier-neutral seat representation."""

    code: str
    row: Optional[int] = None
    column: Optional[str] = None
    price: Optional[float] = None
    status: Optional[str] = None
    available: Optional[bool] = None
    availability_known: bool = False
    seat_type: Optional[str] = None
    aisle: bool = False
    window: Optional[bool] = None
    exit_row: bool = False


@dataclass
class NormalizedSeatMap:
    """Supplier-neutral seat-map response used by the web/mobile clients."""

    seats: List[NormalizedSeat] = field(default_factory=list)
    available_seats: int = 0
    unavailable_seats: int = 0
    availability_known: bool = False
    booking_id: Optional[str] = None
    aircraft: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
