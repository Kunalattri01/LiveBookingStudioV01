from dataclasses import asdict

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..providers.booking_manager import BookingSupplierManager
from ..providers.exceptions import ProviderError, ProviderNotConfiguredError, ProviderUpstreamError


class FlightReviewApiView(APIView):
    """Revalidate selected normalized fare IDs through the active supplier."""

    def post(self, request):
        price_ids = request.data.get("price_ids") or []
        if not isinstance(price_ids, list) or not price_ids or not all(
            isinstance(item, str) and item.strip() for item in price_ids
        ):
            return Response(
                {"success": False, "error_message": "price_ids must be a non-empty list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            review = BookingSupplierManager.get_provider().review(price_ids)
        except ProviderNotConfiguredError as exc:
            return Response(
                {"success": False, "error_code": "flight_provider_not_configured", "error_message": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except ProviderUpstreamError as exc:
            return Response(
                {"success": False, "error_code": "flight_provider_error", "error_message": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except ProviderError as exc:
            return Response(
                {"success": False, "error_code": "flight_provider_error", "error_message": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        normalized = asdict(review)
        request.session["flight_review"] = normalized
        return Response({"success": True, "review": normalized})


class FlightTravellerApiView(APIView):
    """Validate and store traveller details in the server-side session."""

    allowed_passenger_types = {"ADULT", "CHILD", "INFANT"}

    def post(self, request):
        travellers = request.data.get("travellers")
        email = str(request.data.get("email") or "").strip()
        mobile = str(request.data.get("mobile") or "").strip()

        if not isinstance(travellers, list) or not travellers:
            return Response(
                {"success": False, "error_message": "At least one traveller is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cleaned = []
        for index, traveller in enumerate(travellers, start=1):
            if not isinstance(traveller, dict):
                return Response(
                    {"success": False, "error_message": f"Traveller {index} is invalid."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            passenger_type = str(traveller.get("pt") or "ADULT").upper()
            if passenger_type not in self.allowed_passenger_types:
                return Response(
                    {"success": False, "error_message": f"Traveller {index} has an invalid passenger type."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            first_name = str(traveller.get("fN") or "").strip()
            last_name = str(traveller.get("lN") or "").strip()
            title = str(traveller.get("ti") or "").strip()

            if not first_name or not last_name or not title:
                return Response(
                    {"success": False, "error_message": f"Title, first name and last name are required for traveller {index}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cleaned.append({
                "ti": title,
                "fN": first_name,
                "lN": last_name,
                "pt": passenger_type,
                "dob": str(traveller.get("dob") or "").strip() or None,
                "pNat": str(traveller.get("pNat") or "").strip() or None,
                "pNum": str(traveller.get("pNum") or "").strip() or None,
                "eD": str(traveller.get("eD") or "").strip() or None,
            })

        if not email or not mobile:
            return Response(
                {"success": False, "error_message": "Email and mobile number are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.session["flight_travellers"] = {
            "travellers": cleaned,
            "email": email,
            "mobile": mobile,
        }
        request.session.modified = True

        return Response({"success": True, "redirect_url": "/flight/seat-selection/"})


class FlightSeatMapApiView(APIView):
    """Return the seat map for the reviewed itinerary."""

    def post(self, request):
        booking_id = str(request.data.get("booking_id") or "").strip()
        if not booking_id:
            return Response(
                {"success": False, "error_message": "booking_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            seat_map = BookingSupplierManager.get_provider().seat_map(booking_id)
        except ProviderNotConfiguredError as exc:
            return Response(
                {"success": False, "error_code": "flight_provider_not_configured", "error_message": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except ProviderUpstreamError as exc:
            return Response(
                {"success": False, "error_code": "flight_provider_error", "error_message": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except ProviderError as exc:
            return Response(
                {"success": False, "error_code": "flight_provider_error", "error_message": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        normalized = asdict(seat_map)
        request.session["flight_seat_map"] = normalized
        return Response({"success": True, "seat_map": normalized})


class FlightSelectionApiView(APIView):
    """Store the selected flight and fare in the current session."""

    def post(self, request):
        selected = request.data.get("selected")
        search_request = request.data.get("search_request")
        if not isinstance(selected, list) or not selected:
            return Response(
                {"success": False, "error_message": "Select at least one flight."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.session["flight_selection"] = selected
        request.session["flight_search_request"] = search_request or {}
        return Response({"success": True, "redirect_url": "/flight/flight-fare/"})


class ApiFlightFareRule(APIView):
    """Return normalized fare rules through the active supplier adapter."""

    def post(self, request):
        reference_id = str(
            request.data.get("reference_id")
            or request.data.get("fare_rule_reference")
            or request.data.get("id")
            or ""
        ).strip()
        flow_type = str(request.data.get("flow_type") or "SEARCH").strip() or "SEARCH"

        if not reference_id:
            return Response(
                {
                    "success": False,
                    "error_code": "invalid_fare_rule_request",
                    "error_message": "reference_id is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            rules = BookingSupplierManager.get_provider().fare_rule(reference_id, flow_type)
        except ProviderNotConfiguredError as exc:
            return Response(
                {"success": False, "error_code": "flight_provider_not_configured", "error_message": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except ProviderUpstreamError as exc:
            return Response(
                {"success": False, "error_code": "flight_provider_error", "error_message": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"success": True, "fare_rule": rules})

class FlightSeatSelectionApiView(APIView):
    """Persist the user's normalized seat choices in the server session."""

    def post(self, request):
        seats = request.data.get("seats")
        if not isinstance(seats, list):
            return Response(
                {"success": False, "error_message": "seats must be a list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        travellers = request.session.get("flight_travellers", {}).get("travellers", [])
        expected_count = len(travellers)
        if expected_count < 1:
            return Response(
                {"success": False, "error_message": "Traveller details are missing. Please complete the traveller step first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cleaned = []
        passenger_indexes = set()
        seat_codes = set()
        for seat in seats:
            if not isinstance(seat, dict):
                return Response(
                    {"success": False, "error_message": "Each selected seat must be an object."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            code = str(seat.get("code") or "").strip()
            if not code:
                return Response(
                    {"success": False, "error_message": "Every selected seat must have a seat code."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                passenger_index = int(seat.get("passenger_index"))
            except (TypeError, ValueError):
                return Response(
                    {"success": False, "error_message": "Every seat must be assigned to a passenger."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if passenger_index < 0 or passenger_index >= expected_count:
                return Response(
                    {"success": False, "error_message": "A selected seat refers to an invalid passenger."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if passenger_index in passenger_indexes:
                return Response(
                    {"success": False, "error_message": "Each passenger can have only one seat selection."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if code in seat_codes:
                return Response(
                    {"success": False, "error_message": "The same seat cannot be assigned to more than one passenger."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            passenger_indexes.add(passenger_index)
            seat_codes.add(code)
            cleaned.append({
                "passenger_index": passenger_index,
                "passenger_type": travellers[passenger_index].get("pt"),
                "code": code,
                "row": seat.get("row"),
                "column": seat.get("column"),
                "price": seat.get("price"),
            })

        # Some fares just don't come with a seat map at all - that's a
        # normal thing suppliers do, not an error, so we only insist
        # on one seat per traveller when there was actually a seat map
        # to choose from.
        seat_map = request.session.get("flight_seat_map") or {}
        supplier_has_seat_map = bool(seat_map.get("seats"))

        if supplier_has_seat_map and len(cleaned) != expected_count:
            return Response(
                {"success": False, "error_message": f"Please select one seat for each of the {expected_count} travellers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.session["selected_seats"] = cleaned
        request.session.modified = True
        return Response({"success": True, "seats": cleaned})
