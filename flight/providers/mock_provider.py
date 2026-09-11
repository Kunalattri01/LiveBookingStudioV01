from typing import List

from ..services.dto import (
    BaggageInfo,
    FareOption,
    FlightSegment,
    NormalizedFlight,
    SearchRequest,
)
from .base import FlightProvider


class MockFlightProvider(FlightProvider):
    """
    TEST-ONLY provider.

    This class is intentionally NOT registered in SupplierManager and
    is not reachable through any FLIGHT_PROVIDER environment value.
    It exists solely so automated tests can exercise FlightService,
    the API layer, and the normalization contract end-to-end without
    calling TripJack or inventing "real" data for actual users.

    Automated tests must construct this class directly and inject it,
    e.g.:

        service = FlightService(provider=MockFlightProvider())

    Every field returned is clearly labeled as synthetic
    (provider="mock", provider_reference starting with "MOCK-") so it
    can never be confused with real supplier output if it somehow
    leaked into a response - which it must not.
    """

    def search(self, search_request: SearchRequest) -> List[NormalizedFlight]:
        segment = search_request.segments[0]

        return [
            NormalizedFlight(
                provider="mock",
                provider_reference="MOCK-REF-0001",
                leg_label="ONWARD",
                segments=[
                    FlightSegment(
                        segment_id="MOCK-SEG-0001",
                        airline_code="MK",
                        airline_name="Mock Airline",
                        is_lcc=False,
                        flight_number="MK101",
                        aircraft_type="MOCK",
                        origin=segment.origin,
                        destination=segment.destination,
                        departure_time=f"{segment.departure_date}T09:00:00",
                        arrival_time=f"{segment.departure_date}T11:00:00",
                        duration_minutes=120,
                        technical_stops=0,
                    )
                ],
                stops=0,
                total_duration_minutes=120,
                fares=[
                    FareOption(
                        fare_id="MOCK-FARE-ECONOMY",
                        fare_type="regular",
                        cabin_class="ECONOMY",
                        base_fare=4999.0,
                        taxes=850.0,
                        total_fare=5849.0,
                        currency="INR",
                        refundable=False,
                        baggage=BaggageInfo(cabin="7kg", checkin="15kg"),
                        fare_rules_reference="MOCK-RULES-0001",
                    )
                ],
            )
        ]
