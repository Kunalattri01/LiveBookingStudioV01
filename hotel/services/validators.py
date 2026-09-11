import uuid
from datetime import date
from typing import List, Tuple

from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q

from ..models import Hotel
from .booking_dto import DeliveryInfo, GstInfo, HotelBookRequest, RoomTravellerGroup, TravellerInfo
from .dto import (
    VALID_PASSENGER_TYPES,
    VALID_TITLES,
    HotelDetailRequest,
    HotelReviewRequest,
    HotelSearchRequest,
    RoomRequest,
)

MAX_ROOMS = 9
MAX_ADULTS_PER_ROOM = 6
MAX_CHILDREN_PER_ROOM = 4


class ValidationError(Exception):
    """Raised with a list of human-readable error messages."""

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(" ".join(errors))


def _validate_date(raw_value, field_label: str, errors: List[str], allow_past: bool = False):
    if raw_value is None or raw_value == "":
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


def _parse_rooms(payload: dict, errors: List[str]) -> List[RoomRequest]:
    raw_rooms = payload.get("rooms")

    if raw_rooms is None:
        # Legacy homepage-form fallback: total guest count + room count,
        # distributed as evenly as possible across the rooms.
        try:
            total_guests = int(payload.get("guests", 2))
            room_count = int(payload.get("room_count", payload.get("rooms_count", 1)))
        except (TypeError, ValueError):
            errors.append("Invalid guest or room count.")
            return []

        if room_count < 1:
            errors.append("At least one room is required.")
            return []

        base, remainder = divmod(total_guests, room_count)
        raw_rooms = [
            {"adults": base + (1 if i < remainder else 0)} for i in range(room_count)
        ]
        raw_rooms = [r for r in raw_rooms if r["adults"] > 0] or [{"adults": 1}]

    if not isinstance(raw_rooms, list) or not raw_rooms:
        errors.append("At least one room is required.")
        return []

    if len(raw_rooms) > MAX_ROOMS:
        errors.append(f"A maximum of {MAX_ROOMS} rooms is supported.")
        return []

    rooms: List[RoomRequest] = []

    for index, raw_room in enumerate(raw_rooms, start=1):
        if not isinstance(raw_room, dict):
            errors.append(f"Room {index} is invalid.")
            continue

        try:
            adults = int(raw_room.get("adults", 1))
        except (TypeError, ValueError):
            errors.append(f"Room {index} has an invalid adult count.")
            continue

        try:
            children = int(raw_room.get("children", 0))
        except (TypeError, ValueError):
            errors.append(f"Room {index} has an invalid child count.")
            continue

        if not (1 <= adults <= MAX_ADULTS_PER_ROOM):
            errors.append(f"Room {index}: adults must be between 1 and {MAX_ADULTS_PER_ROOM}.")
        if not (0 <= children <= MAX_CHILDREN_PER_ROOM):
            errors.append(f"Room {index}: children must be between 0 and {MAX_CHILDREN_PER_ROOM}.")

        raw_ages = raw_room.get("child_ages") or raw_room.get("childAge") or []
        child_ages: List[int] = []

        if children:
            if not isinstance(raw_ages, list) or len(raw_ages) != children:
                errors.append(f"Room {index}: please provide one age (0-17) for each child.")
            else:
                for age in raw_ages:
                    try:
                        age_int = int(age)
                    except (TypeError, ValueError):
                        errors.append(f"Room {index}: child age must be a whole number.")
                        continue
                    if not (0 <= age_int <= 17):
                        errors.append(f"Room {index}: child age must be between 0 and 17.")
                    child_ages.append(age_int)

        rooms.append(RoomRequest(adults=adults, children=children, child_ages=child_ages))

    return rooms


def _resolve_hids(destination: str, errors: List[str]) -> List[str]:
    destination = (destination or "").strip()

    if not destination:
        errors.append("Please enter a destination.")
        return []

    matches = (
        Hotel.objects.filter(is_active=True)
        .filter(Q(city__icontains=destination) | Q(name__icontains=destination))
        .order_by("-is_popular", "name")
        .values_list("tj_hotel_id", flat=True)[:100]
    )
    hids = list(matches)

    if not hids:
        errors.append(f"No properties found for '{destination}' in our current catalog.")

    return hids


def _validate_currency(payload: dict, errors: List[str]) -> str:
    from django.conf import settings

    currency = (payload.get("currency") or getattr(settings, "DEFAULT_CURRENCY", "INR")).strip().upper()
    if len(currency) != 3 or not currency.isalpha():
        errors.append("Invalid currency code.")
        currency = "INR"
    return currency


def validate_search_payload(payload: dict) -> Tuple[HotelSearchRequest, List[str]]:
    """
    Validates a hotel Listing (search) request coming from either the
    web form or the JSON API and returns (HotelSearchRequest, errors).

    If errors is non-empty, the request may be incomplete and must not
    be used.
    """

    errors: List[str] = []

    destination = (payload.get("destination") or "").strip()
    hids = payload.get("hids")

    if isinstance(hids, list) and hids:
        hids = [str(h).strip() for h in hids if str(h).strip()]
    else:
        hids = _resolve_hids(destination, errors)

    check_in = _validate_date(payload.get("check_in") or payload.get("checkIn"), "check-in date", errors)
    check_out = _validate_date(payload.get("check_out") or payload.get("checkOut"), "check-out date", errors)

    if check_in and check_out and check_out <= check_in:
        errors.append("Check-out date must be after check-in date.")

    rooms = _parse_rooms(payload, errors)
    currency = _validate_currency(payload, errors)
    nationality = str(payload.get("nationality") or "106").strip()

    search_request = HotelSearchRequest(
        destination=destination,
        check_in=check_in or date.today(),
        check_out=check_out or date.today(),
        rooms=rooms,
        hids=hids,
        currency=currency,
        nationality=nationality,
        correlation_id=uuid.uuid4().hex,
    )

    return search_request, errors


def validate_detail_payload(payload: dict) -> Tuple[HotelDetailRequest, List[str]]:
    """Validates a Dynamic Detail (Pricing) request. correlation_id must be carried over from Listing."""

    errors: List[str] = []

    hid = str(payload.get("hid") or "").strip()
    if not hid:
        errors.append("A hotel is required.")

    correlation_id = str(payload.get("correlation_id") or payload.get("correlationId") or "").strip()
    if not correlation_id:
        errors.append("A correlation ID from the search results is required.")

    check_in = _validate_date(payload.get("check_in") or payload.get("checkIn"), "check-in date", errors)
    check_out = _validate_date(payload.get("check_out") or payload.get("checkOut"), "check-out date", errors)

    if check_in and check_out and check_out <= check_in:
        errors.append("Check-out date must be after check-in date.")

    rooms = _parse_rooms(payload, errors)
    currency = _validate_currency(payload, errors)
    nationality = str(payload.get("nationality") or "106").strip()

    detail_request = HotelDetailRequest(
        hid=hid,
        check_in=check_in or date.today(),
        check_out=check_out or date.today(),
        rooms=rooms,
        correlation_id=correlation_id,
        currency=currency,
        nationality=nationality,
    )

    return detail_request, errors


def validate_review_payload(payload: dict) -> Tuple[HotelReviewRequest, List[str]]:
    errors: List[str] = []

    correlation_id = str(payload.get("correlation_id") or payload.get("correlationId") or "").strip()
    option_id = str(payload.get("option_id") or payload.get("optionId") or "").strip()
    review_hash = str(payload.get("review_hash") or payload.get("reviewHash") or "").strip()
    hid = str(payload.get("hid") or "").strip()

    if not correlation_id:
        errors.append("A correlation ID from the search results is required.")
    if not option_id:
        errors.append("Please select a room/rate option.")
    if not review_hash:
        errors.append("A review hash from the hotel details is required.")
    if not hid:
        errors.append("A hotel is required.")

    review_request = HotelReviewRequest(
        correlation_id=correlation_id, option_id=option_id, review_hash=review_hash, hid=hid
    )

    return review_request, errors


def _validate_travellers(payload: dict, errors: List[str]) -> List[RoomTravellerGroup]:
    raw_groups = payload.get("room_traveller_info") or payload.get("roomTravellerInfo")

    if not isinstance(raw_groups, list) or not raw_groups:
        errors.append("Traveller details are required for every room.")
        return []

    groups: List[RoomTravellerGroup] = []

    for room_index, raw_group in enumerate(raw_groups, start=1):
        raw_travellers = (raw_group or {}).get("travellers") or (raw_group or {}).get("travellerInfo") or []

        if not isinstance(raw_travellers, list) or not raw_travellers:
            errors.append(f"Room {room_index}: at least one traveller is required.")
            continue

        travellers: List[TravellerInfo] = []

        for guest_index, raw_traveller in enumerate(raw_travellers, start=1):
            if not isinstance(raw_traveller, dict):
                errors.append(f"Room {room_index}, guest {guest_index} is invalid.")
                continue

            title = str(raw_traveller.get("title") or raw_traveller.get("ti") or "").strip()
            passenger_type = str(
                raw_traveller.get("passenger_type") or raw_traveller.get("pt") or ""
            ).strip().upper()
            first_name = str(raw_traveller.get("first_name") or raw_traveller.get("fN") or "").strip()
            last_name = str(raw_traveller.get("last_name") or raw_traveller.get("lN") or "").strip()
            pan = str(raw_traveller.get("pan") or "").strip() or None
            passport_number = str(
                raw_traveller.get("passport_number") or raw_traveller.get("pNum") or ""
            ).strip() or None

            if title not in VALID_TITLES:
                errors.append(f"Room {room_index}, guest {guest_index}: invalid title.")
            if passenger_type not in VALID_PASSENGER_TYPES:
                errors.append(f"Room {room_index}, guest {guest_index}: invalid passenger type.")
            if not first_name or not last_name:
                errors.append(f"Room {room_index}, guest {guest_index}: first and last name are required.")

            travellers.append(
                TravellerInfo(
                    title=title,
                    passenger_type=passenger_type,
                    first_name=first_name,
                    last_name=last_name,
                    pan=pan,
                    passport_number=passport_number,
                )
            )

        groups.append(RoomTravellerGroup(travellers=travellers))

    return groups


def _validate_delivery_info(payload: dict, errors: List[str]) -> DeliveryInfo:
    raw = payload.get("delivery_info") or payload.get("deliveryInfo") or {}

    emails = raw.get("emails") or []
    contacts = raw.get("contacts") or []
    codes = raw.get("codes") or raw.get("code") or []

    if not isinstance(emails, list) or not emails:
        errors.append("At least one email address is required.")
    else:
        for email in emails:
            try:
                validate_email(str(email))
            except DjangoValidationError:
                errors.append(f"'{email}' is not a valid email address.")

    if not isinstance(contacts, list) or not contacts:
        errors.append("At least one contact number is required.")

    if not isinstance(codes, list) or len(codes) != len(contacts):
        errors.append("Please provide a dialing code for every contact number.")

    return DeliveryInfo(
        emails=[str(e) for e in emails] if isinstance(emails, list) else [],
        contacts=[str(c) for c in contacts] if isinstance(contacts, list) else [],
        codes=[str(c) for c in codes] if isinstance(codes, list) else [],
    )


def validate_book_payload(payload: dict) -> Tuple[HotelBookRequest, List[str]]:
    errors: List[str] = []

    booking_id = str(payload.get("booking_id") or payload.get("bookingId") or "").strip()
    if not booking_id:
        errors.append("A booking ID from the review step is required.")

    room_traveller_info = _validate_travellers(payload, errors)
    delivery_info = _validate_delivery_info(payload, errors)

    raw_gst = payload.get("gst_info") or payload.get("gstInfo")
    gst_info = None
    if isinstance(raw_gst, dict) and (raw_gst.get("gst_number") or raw_gst.get("gstNumber")):
        gst_info = GstInfo(
            gst_number=str(raw_gst.get("gst_number") or raw_gst.get("gstNumber") or "").strip(),
            registered_name=str(raw_gst.get("registered_name") or raw_gst.get("registeredName") or "").strip(),
        )

    amount = payload.get("amount")
    if amount is not None:
        try:
            amount = float(amount)
            if amount <= 0:
                errors.append("Amount must be greater than zero.")
        except (TypeError, ValueError):
            errors.append("Invalid amount.")
            amount = None

    book_request = HotelBookRequest(
        booking_id=booking_id,
        room_traveller_info=room_traveller_info,
        delivery_info=delivery_info,
        gst_info=gst_info,
        amount=amount,
    )

    return book_request, errors
