"""TripJack -> application booking-data normalization.

Only this module knows the TripJack field names used after flight search.
Views and browser code consume the provider-neutral structures returned here.
"""

import re
from typing import Any, Dict, Iterable, List, Optional

from ..services.booking import NormalizedReview, NormalizedSeat, NormalizedSeatMap
from .booking import BookingNormalizer


class TripJackBookingNormalizer(BookingNormalizer):
    """Normalize TripJack review, seat-map and fare-rule responses."""

    _SEAT_CONTAINER_KEYS = {
        "seat",
        "seats",
        "seatinfo",
        "seatInfo",
        "seatMap",
        "seatmap",
        "seatLayout",
        "seatlayout",
        "layout",
    }

    def normalize_review(self, raw_response: Dict[str, Any]) -> NormalizedReview:
        booking_id = self._find_value(raw_response, {"bookingId", "bookingID", "booking_id"})
        total = self._find_value(raw_response, {"TF", "totalFare", "total_fare"})
        passport = self._find_value(
            raw_response,
            {"passportRequired", "passport_required", "isPassportRequired"},
        )
        seats_available = self._find_value(
            raw_response,
            {"seatsAvailable", "seats_available", "seatRemaining", "seatRemains", "sR"},
        )

        return NormalizedReview(
            booking_id=str(booking_id) if booking_id not in (None, "") else None,
            total_fare=total,
            passport_required=self._as_bool(passport),
            seats_available=self._as_int(seats_available),
            raw_status=self._find_value(raw_response, {"status"}),
            data={},
        )

    def normalize_fare_rule(self, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        # Fare-rule content is intentionally preserved as structured data,
        # while supplier-specific names remain behind the normalizer boundary.
        if not isinstance(raw_response, dict):
            return {"rules": []}

        rules = []
        candidates = raw_response.get("fareRule") or raw_response.get("fareRules")
        if candidates is None:
            candidates = raw_response.get("data")

        if isinstance(candidates, list):
            rules = candidates
        elif isinstance(candidates, dict):
            rules = [candidates]
        elif candidates not in (None, ""):
            rules = [{"description": str(candidates)}]

        return {"rules": rules}

    def normalize_seat_map(self, raw_response: Dict[str, Any]) -> NormalizedSeatMap:
        if not isinstance(raw_response, dict):
            return NormalizedSeatMap()

        nodes: List[dict] = []
        self._collect_seat_nodes(raw_response, nodes)

        seats: List[NormalizedSeat] = []
        seen = set()
        for node in nodes:
            seat = self._normalize_seat(node)
            if seat is None:
                continue
            dedupe_key = (seat.code, seat.row, seat.column)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            seats.append(seat)

        seats.sort(key=self._seat_sort_key)
        known = [seat for seat in seats if seat.availability_known]
        available_count = sum(seat.available is True for seat in known)
        unavailable_count = sum(seat.available is False for seat in known)

        return NormalizedSeatMap(
            seats=seats,
            available_seats=available_count,
            unavailable_seats=unavailable_count,
            availability_known=bool(known),
            booking_id=self._find_value(raw_response, {"bookingId", "bookingID", "booking_id"}),
            aircraft=self._find_value(raw_response, {"aircraft", "aircraftType", "equipment"}),
            data={},
        )

    def _collect_seat_nodes(self, value: Any, output: List[dict]) -> None:
        if isinstance(value, list):
            for item in value:
                self._collect_seat_nodes(item, output)
            return

        if not isinstance(value, dict):
            return

        if self._looks_like_seat(value):
            output.append(value)

        for key, child in value.items():
            # Explicit seat containers are traversed just like ordinary
            # objects. We keep this branch for readability/documentation and
            # future supplier variants rather than making assumptions about
            # one exact TripJack seat-map shape.
            if key in self._SEAT_CONTAINER_KEYS:
                self._collect_seat_nodes(child, output)
            elif isinstance(child, (dict, list)):
                self._collect_seat_nodes(child, output)

    @staticmethod
    def _looks_like_seat(value: dict) -> bool:
        code = value.get("code") or value.get("seatCode") or value.get("seatNo") or value.get("number")
        has_seat_signal = any(
            key in value
            for key in (
                "isAvailable",
                "isBooked",
                "available",
                "status",
                "seatStatus",
                "seatType",
                "price",
                "amount",
                "row",
                "column",
            )
        )
        return code not in (None, "") and has_seat_signal

    def _normalize_seat(self, value: dict) -> Optional[NormalizedSeat]:
        raw_code = value.get("code") or value.get("seatCode") or value.get("seatNo") or value.get("number")
        if raw_code in (None, ""):
            return None

        code = str(raw_code).strip()
        position = value.get("seatPosition") or value.get("position") or {}
        row = self._as_int(value.get("row"))
        column = value.get("column") or value.get("col") or value.get("seatColumn")

        if isinstance(position, dict):
            if row is None:
                row = self._as_int(position.get("row"))
            if column in (None, ""):
                column = position.get("column") or position.get("col")

        column = str(column).strip().upper() if column not in (None, "") else None

        if row is None or column is None:
            parsed_row, parsed_column = self._parse_seat_code(code)
            row = row if row is not None else parsed_row
            column = column if column is not None else parsed_column

        # TripJack's documented seat-map response uses isBooked. A seat
        # explicitly marked as booked is unavailable; an explicitly
        # unbooked seat is available. Other supplier-neutral aliases are
        # accepted for compatibility with future response variants.
        if "isBooked" in value:
            raw_available = not bool(self._as_bool(value.get("isBooked")))
        else:
            raw_available = value.get("isAvailable")
            if raw_available is None:
                raw_available = value.get("available")
            if raw_available is None:
                raw_available = value.get("isSeatAvailable")

        status = value.get("status") or value.get("seatStatus") or value.get("availability")
        available = self._seat_availability(raw_available, status)
        availability_known = available is not None

        aisle_value = value.get("aisle", value.get("isAisle"))
        if aisle_value is None and isinstance(position, dict):
            aisle_value = position.get("aisle", position.get("isAisle"))

        return NormalizedSeat(
            code=code,
            row=row,
            column=column,
            price=self._as_number(value.get("price", value.get("amount"))),
            status=str(status) if status not in (None, "") else ("BOOKED" if value.get("isBooked") is True else "AVAILABLE" if value.get("isBooked") is False else None),
            available=available,
            availability_known=availability_known,
            seat_type=value.get("seatType") or value.get("type"),
            aisle=self._as_bool(aisle_value) is True,
            window=self._as_bool(value.get("window", value.get("isWindow"))),
            exit_row=self._as_bool(value.get("exitRow", value.get("isExitRow"))) is True,
        )

    @staticmethod
    def _seat_availability(raw_available: Any, status: Any) -> Optional[bool]:
        if raw_available is not None:
            return TripJackBookingNormalizer._as_bool(raw_available)

        if status in (None, ""):
            return None

        normalized = str(status).strip().lower().replace("_", " ")
        if normalized in {"available", "free", "open", "vacant", "bookable", "true", "1"}:
            return True
        if normalized in {
            "occupied",
            "unavailable",
            "not available",
            "blocked",
            "booked",
            "reserved",
            "sold",
            "false",
            "0",
        }:
            return False
        return None

    @staticmethod
    def _parse_seat_code(code: str):
        match = re.match(r"^(\d+)\s*([A-Za-z]+)$", code)
        if not match:
            return None, None
        return int(match.group(1)), match.group(2).upper()

    @staticmethod
    def _seat_sort_key(seat: NormalizedSeat):
        return (seat.row if seat.row is not None else 9999, seat.column or seat.code)

    @staticmethod
    def _as_int(value: Any) -> Optional[int]:
        try:
            return int(value) if value not in (None, "") else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _as_number(value: Any):
        try:
            return float(value) if value not in (None, "") else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _as_bool(value: Any) -> Optional[bool]:
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        normalized = str(value).strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False
        return None

    @staticmethod
    def _find_value(value: Any, keys: set[str]):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in keys and item not in (None, ""):
                    return item
            for item in value.values():
                found = TripJackBookingNormalizer._find_value(item, keys)
                if found not in (None, ""):
                    return found
        elif isinstance(value, list):
            for item in value:
                found = TripJackBookingNormalizer._find_value(item, keys)
                if found not in (None, ""):
                    return found
        return None
