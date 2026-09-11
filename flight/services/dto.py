from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional

VALID_TRIP_TYPES = ("oneway", "roundtrip", "multicity")
VALID_CABIN_CLASSES = ("economy", "premium_economy", "business", "first")


@dataclass
class FlightSegmentRequest:
    """
    One origin -> destination leg on a given date.

    A one-way search is a single segment. A round trip is represented
    as two segments (outbound, return) OR as origin/destination/dates
    at the top level of SearchRequest (kept for backward compatibility
    with the existing oneway/roundtrip request shape). Multi-city uses
    a list of these with independent origin/destination/date per leg.
    """

    origin: str
    destination: str
    departure_date: date


@dataclass
class SearchRequest:
    """
    Stable internal representation of a flight search, independent of
    any supplier and independent of how the request arrived (web form,
    JSON API, mobile app).
    """

    trip_type: str
    segments: List[FlightSegmentRequest]
    adults: int = 1
    children: int = 0
    infants: int = 0
    cabin_class: str = "economy"
    special_fare: Optional[str] = None

    @property
    def origin(self) -> Optional[str]:
        """Convenience accessor for oneway/roundtrip (first segment)."""
        return self.segments[0].origin if self.segments else None

    @property
    def destination(self) -> Optional[str]:
        return self.segments[0].destination if self.segments else None

    @property
    def departure_date(self) -> Optional[date]:
        return self.segments[0].departure_date if self.segments else None

    @property
    def return_date(self) -> Optional[date]:
        """Only meaningful for trip_type == 'roundtrip' (second segment)."""
        if self.trip_type == "roundtrip" and len(self.segments) > 1:
            return self.segments[1].departure_date
        return None


@dataclass
class BaggageInfo:
    cabin: Optional[str] = None
    checkin: Optional[str] = None


@dataclass
class FareOption:
    """
    One bookable fare for a flight. Fields default to None/unset rather
    than a guessed value when a supplier doesn't provide them - we do
    not invent data.

    Field provenance (TripJack UAT `air-search-all`, per verified
    sample response - see docs/tripjack-integration.md). Note that
    cB/fB/cc/rT/sR/mI are siblings of `fC` on the ADULT object, not
    nested inside it:
        fare_id             <- totalPriceList[].id
        fare_type           <- totalPriceList[].fareIdentifier
        cabin_class         <- totalPriceList[].fd.ADULT.cc
        booking_class       <- totalPriceList[].fd.ADULT.cB (RBD letter)
        fare_basis          <- totalPriceList[].fd.ADULT.fB
        base_fare           <- totalPriceList[].fd.ADULT.fC.BF
        taxes               <- totalPriceList[].fd.ADULT.fC.TAF
        total_fare          <- totalPriceList[].fd.ADULT.fC.TF
        net_fare            <- totalPriceList[].fd.ADULT.fC.NF
        seats_available     <- totalPriceList[].fd.ADULT.sR
        meal_included       <- totalPriceList[].fd.ADULT.mI
        refund_type_code    <- totalPriceList[].fd.ADULT.rT
        baggage.checkin     <- totalPriceList[].fd.ADULT.bI.iB
        baggage.cabin       <- totalPriceList[].fd.ADULT.bI.cB
    """

    fare_id: Optional[str] = None
    fare_type: Optional[str] = None
    cabin_class: Optional[str] = None
    booking_class: Optional[str] = None
    fare_basis: Optional[str] = None
    base_fare: Optional[float] = None
    taxes: Optional[float] = None
    total_fare: Optional[float] = None
    net_fare: Optional[float] = None
    currency: Optional[str] = None
    seats_available: Optional[int] = None
    meal_included: Optional[bool] = None
    refundable: Optional[bool] = None
    refund_type_code: Optional[int] = None
    baggage: Optional[BaggageInfo] = None
    fare_rules_reference: Optional[str] = None


@dataclass
class FlightSegment:
    """
    Field provenance (TripJack UAT `air-search-all` `sI[]` entries):
        segment_id          <- sI[].id
        airline_code        <- sI[].fD.aI.code
        airline_name        <- sI[].fD.aI.name
        is_lcc              <- sI[].fD.aI.isLcc
        flight_number       <- sI[].fD.fN
        aircraft_type       <- sI[].fD.eT
        origin              <- sI[].da.code
        origin_city         <- sI[].da.city
        origin_terminal     <- sI[].da.terminal (not always present)
        destination         <- sI[].aa.code
        destination_city    <- sI[].aa.city
        destination_terminal <- sI[].aa.terminal (not always present)
        departure_time      <- sI[].dt
        arrival_time        <- sI[].at
        duration_minutes    <- sI[].duration
        technical_stops     <- sI[].stops (stops within this flight number)
        stopovers           <- sI[].so
    """

    segment_id: Optional[str] = None
    airline_code: Optional[str] = None
    airline_name: Optional[str] = None
    is_lcc: Optional[bool] = None
    flight_number: Optional[str] = None
    aircraft_type: Optional[str] = None
    origin: Optional[str] = None
    origin_city: Optional[str] = None
    origin_terminal: Optional[str] = None
    destination: Optional[str] = None
    destination_city: Optional[str] = None
    destination_terminal: Optional[str] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    technical_stops: Optional[int] = None
    stopovers: List[dict] = field(default_factory=list)


@dataclass
class NormalizedFlight:
    """
    Our stable, supplier-independent flight representation. This is
    what the frontend and mobile clients consume - never raw supplier
    JSON.

    `stops` is the number of connections between segments in this
    itinerary (len(segments) - 1) - distinct from each segment's own
    `technical_stops`.

    `leg_label` identifies which journey leg this option belongs to
    for round-trip/multi-city searches (e.g. the outbound leg vs. the
    return leg vs. a later multi-city leg). For TripJack specifically,
    this is whatever direction key it returned under `tripInfos`
    (verified: "ONWARD" for the first/only leg; other leg key names
    for round-trip/multi-city are not verified against a real
    response - see docs/tripjack-integration.md). `None` for providers
    that don't have this concept. Selecting one option per leg and
    combining them into a single bookable itinerary is a later
    (out-of-scope) Review/Revalidate step.
    """

    provider: str
    provider_reference: Optional[str] = None
    leg_label: Optional[str] = None
    segments: List[FlightSegment] = field(default_factory=list)
    stops: Optional[int] = None
    total_duration_minutes: Optional[int] = None
    fares: List[FareOption] = field(default_factory=list)


@dataclass
class SearchResult:
    """
    Outcome of a flight search through FlightService. Either a list of
    normalized flights, or a controlled error - never both, never a
    silent fallback to fake data.
    """

    success: bool
    flights: List[NormalizedFlight] = field(default_factory=list)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
