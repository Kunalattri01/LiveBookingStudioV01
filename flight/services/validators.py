from datetime import date
from typing import List, Tuple

from ..models import Airport
from .dto import (
    VALID_CABIN_CLASSES,
    VALID_TRIP_TYPES,
    FlightSegmentRequest,
    SearchRequest,
)


class ValidationError(Exception):
    """Raised with a list of human-readable error messages."""

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(" ".join(errors))


def _validate_airport_code(code: str, field_label: str, errors: List[str]):
    if not code:
        errors.append(f"Please provide a valid {field_label}.")
        return None

    airport = Airport.objects.filter(code=code.strip().upper(), is_active=True).first()

    if not airport:
        errors.append(f"Unknown {field_label} airport code: {code}.")

    return airport


def _validate_date(raw_value, field_label: str, errors: List[str], allow_past: bool = False):
    if raw_value is None:
        errors.append(f"Please provide a valid {field_label}.")
        return None

    if isinstance(raw_value, date):
        parsed = raw_value
    else:
        from django.utils.dateparse import parse_date

        parsed = parse_date(str(raw_value))

    if not parsed:
        errors.append(f"Invalid {field_label} format.")
        return None

    if not allow_past and parsed < date.today():
        errors.append(f"{field_label} cannot be in the past.")

    return parsed


def validate_search_payload(payload: dict) -> Tuple[SearchRequest, List[str]]:
    """
    Validates a flight search request coming from either the web form
    or the JSON API and returns (SearchRequest, errors).

    If errors is non-empty, the SearchRequest may be incomplete and
    must not be used.
    """

    errors: List[str] = []

    trip_type = (payload.get("trip_type") or "oneway").strip().lower()

    if trip_type not in VALID_TRIP_TYPES:
        errors.append("Invalid trip type.")
        trip_type = "oneway"

    try:
        adults = int(payload.get("adults", 1))
        children = int(payload.get("children", 0))
        infants = int(payload.get("infants", 0))
    except (TypeError, ValueError):
        errors.append("Invalid traveller counts.")
        adults, children, infants = 1, 0, 0

    if not (1 <= adults <= 9):
        errors.append("Adults must be between 1 and 9.")
    if not (0 <= children <= 9):
        errors.append("Children must be between 0 and 9.")
    if not (0 <= infants <= adults):
        errors.append("Infants cannot exceed the number of adults.")

    cabin_class = (payload.get("cabin_class") or "economy").strip().lower()
    if cabin_class not in VALID_CABIN_CLASSES:
        errors.append("Invalid cabin class.")
        cabin_class = "economy"

    special_fare = payload.get("special_fare") or "regular"

    segments: List[FlightSegmentRequest] = []

    if trip_type in ("oneway", "roundtrip"):
        origin_airport = _validate_airport_code(payload.get("origin", ""), "departure", errors)
        destination_airport = _validate_airport_code(payload.get("destination", ""), "destination", errors)

        if (
            origin_airport
            and destination_airport
            and origin_airport.code == destination_airport.code
        ):
            errors.append("Departure and destination cannot be the same.")

        departure_date = _validate_date(payload.get("departure_date"), "departure date", errors)

        if origin_airport and destination_airport and departure_date:
            segments.append(
                FlightSegmentRequest(
                    origin=origin_airport.code,
                    destination=destination_airport.code,
                    departure_date=departure_date,
                )
            )

        if trip_type == "roundtrip":
            return_date = _validate_date(payload.get("return_date"), "return date", errors)

            if return_date and departure_date and return_date < departure_date:
                errors.append("Return date cannot be before departure date.")

            if origin_airport and destination_airport and return_date:
                segments.append(
                    FlightSegmentRequest(
                        origin=destination_airport.code,
                        destination=origin_airport.code,
                        departure_date=return_date,
                    )
                )

    elif trip_type == "multicity":
        raw_segments = payload.get("segments") or []

        if not isinstance(raw_segments, list) or len(raw_segments) < 2:
            errors.append("Multi-city search requires at least two segments.")
        elif len(raw_segments) > 6:
            errors.append("Multi-city search supports a maximum of 6 segments.")
        else:
            previous_date = None

            for index, raw_segment in enumerate(raw_segments, start=1):
                if not isinstance(raw_segment, dict):
                    errors.append(f"Segment {index} is invalid.")
                    continue

                origin_airport = _validate_airport_code(
                    raw_segment.get("origin", ""), f"segment {index} departure", errors
                )
                destination_airport = _validate_airport_code(
                    raw_segment.get("destination", ""), f"segment {index} destination", errors
                )

                if (
                    origin_airport
                    and destination_airport
                    and origin_airport.code == destination_airport.code
                ):
                    errors.append(f"Segment {index}: departure and destination cannot be the same.")

                segment_date = _validate_date(
                    raw_segment.get("departure_date"), f"segment {index} departure date", errors
                )

                if segment_date and previous_date and segment_date < previous_date:
                    errors.append(f"Segment {index} date cannot be before the previous segment.")

                if segment_date:
                    previous_date = segment_date

                if origin_airport and destination_airport and segment_date:
                    segments.append(
                        FlightSegmentRequest(
                            origin=origin_airport.code,
                            destination=destination_airport.code,
                            departure_date=segment_date,
                        )
                    )

    search_request = SearchRequest(
        trip_type=trip_type,
        segments=segments,
        adults=adults,
        children=children,
        infants=infants,
        cabin_class=cabin_class,
        special_fare=special_fare,
    )

    return search_request, errors
