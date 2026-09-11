"""
TripJack normalizer.

One-way (leg key "ONWARD") is implemented against a real, verified
TripJack UAT `air-search-all` response (see
flight/tests/fixtures/tripjack_air_search_all_sample.json and
docs/tripjack-integration.md for the full provenance). Field mappings
are documented on the DTO classes themselves (flight/services/dto.py).

Round-trip/multi-city: the per-itinerary field mapping below (`sI`,
`totalPriceList`, etc.) is reused unchanged, since that structure is
part of what's verified. What is NOT verified is which additional key
names TripJack uses in `tripInfos` for legs beyond the first (e.g.
whether a return leg is called "RETURN"). Rather than guess a specific
key name, this normalizer iterates every key actually present in
`tripInfos` and tags each resulting NormalizedFlight with that key as
`leg_label` - see flight/tests/test_tripjack_normalizer.py for a test
using a constructed (not captured) multi-leg fixture that exercises
this generalization.

This module never invents a value: every field on NormalizedFlight/
FlightSegment/FareOption defaults to None (or an empty list) and is
only populated when the corresponding TripJack field is actually
present in the response.
"""

from typing import List

from ..services.dto import BaggageInfo, FareOption, FlightSegment, NormalizedFlight
from .base import Normalizer


class TripJackNormalizationError(Exception):
    """Raised when a TripJack response is missing expected top-level structure."""


class TripJackNormalizer(Normalizer):
    def normalize(self, raw_response: dict) -> List[NormalizedFlight]:
        if not isinstance(raw_response, dict) or "searchResult" not in raw_response:
            raise TripJackNormalizationError(
                "TripJack response is missing the expected 'searchResult' key."
            )

        trip_infos = raw_response.get("searchResult", {}).get("tripInfos", {})

        if not isinstance(trip_infos, dict):
            raise TripJackNormalizationError(
                "TripJack response's 'tripInfos' is not the expected object shape."
            )

        # Iterate every leg key TripJack actually returned (verified:
        # "ONWARD" for one-way; round-trip/multi-city may return
        # additional keys whose exact names are unverified - iterating
        # generically avoids guessing what they're called while still
        # handling them correctly whenever present).
        flights = []
        for leg_label, itineraries in trip_infos.items():
            if not isinstance(itineraries, list):
                continue
            for itinerary in itineraries:
                flights.append(self._normalize_itinerary(itinerary, leg_label))

        return flights

    def _normalize_itinerary(self, itinerary: dict, leg_label: str) -> NormalizedFlight:
        raw_segments = itinerary.get("sI", [])

        segments = [self._normalize_segment(sI) for sI in raw_segments]
        fares = [self._normalize_fare(price) for price in itinerary.get("totalPriceList", [])]

        segment_ids = [s.segment_id for s in segments if s.segment_id]
        total_duration = sum(
            s.duration_minutes for s in segments if isinstance(s.duration_minutes, int)
        )

        return NormalizedFlight(
            provider="tripjack",
            provider_reference="+".join(segment_ids) if segment_ids else None,
            leg_label=leg_label,
            segments=segments,
            stops=max(len(raw_segments) - 1, 0),
            total_duration_minutes=total_duration or None,
            fares=fares,
        )

    def _normalize_segment(self, sI: dict) -> FlightSegment:
        fD = sI.get("fD", {}) or {}
        aI = fD.get("aI", {}) or {}
        da = sI.get("da", {}) or {}
        aa = sI.get("aa", {}) or {}

        return FlightSegment(
            segment_id=sI.get("id"),
            airline_code=aI.get("code"),
            airline_name=aI.get("name"),
            is_lcc=aI.get("isLcc"),
            flight_number=fD.get("fN"),
            aircraft_type=fD.get("eT"),
            origin=da.get("code"),
            origin_city=da.get("city"),
            origin_terminal=da.get("terminal"),
            destination=aa.get("code"),
            destination_city=aa.get("city"),
            destination_terminal=aa.get("terminal"),
            departure_time=sI.get("dt"),
            arrival_time=sI.get("at"),
            duration_minutes=sI.get("duration"),
            technical_stops=sI.get("stops"),
            stopovers=sI.get("so") or [],
        )

    def _normalize_fare(self, price: dict) -> FareOption:
        adult_fd = (price.get("fd", {}) or {}).get("ADULT", {}) or {}
        fC = adult_fd.get("fC", {}) or {}
        bI = adult_fd.get("bI", {}) or {}

        baggage = None
        if bI:
            baggage = BaggageInfo(cabin=bI.get("cB"), checkin=bI.get("iB"))

        return FareOption(
            fare_id=price.get("id"),
            fare_type=price.get("fareIdentifier"),
            cabin_class=adult_fd.get("cc"),
            booking_class=adult_fd.get("cB"),
            fare_basis=adult_fd.get("fB"),
            base_fare=fC.get("BF"),
            taxes=fC.get("TAF"),
            total_fare=fC.get("TF"),
            net_fare=fC.get("NF"),
            currency=None,  # not present in the verified response
            seats_available=adult_fd.get("sR"),
            meal_included=adult_fd.get("mI"),
            # "rT" (refund type code) is present in the verified
            # response but its 0/1 semantics are not documented -
            # passed through raw rather than guessed as True/False.
            refundable=None,
            refund_type_code=adult_fd.get("rT"),
            baggage=baggage,
            fare_rules_reference=None,  # not present in the verified response
        )
