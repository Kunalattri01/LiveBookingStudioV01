from dataclasses import asdict

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..providers.booking_manager import BookingSupplierManager
from ..providers.exceptions import ProviderError, ProviderNotConfiguredError, ProviderUpstreamError
from ..services.dto import HotelReviewResult
from ..services.hotel_service import HotelService
from ..services.validators import validate_book_payload, validate_review_payload

_STATUS_CODE_BY_ERROR = {
    "hotel_provider_not_configured": status.HTTP_503_SERVICE_UNAVAILABLE,
    "provider_request_not_supported": status.HTTP_501_NOT_IMPLEMENTED,
    "hotel_provider_error": status.HTTP_502_BAD_GATEWAY,
}


def _error_response(error_code, error_message):
    http_status = _STATUS_CODE_BY_ERROR.get(error_code, status.HTTP_503_SERVICE_UNAVAILABLE)
    return Response(
        {"success": False, "error_code": error_code, "error_message": error_message},
        status=http_status,
    )


class HotelReviewApiView(APIView):
    """
    POST /api/v1/hotels/review/

    Step 3 - re-validates the selected option's price/availability and
    returns the bookingId required by the Book step. Must be called
    immediately before Book; the normalized review is also stashed in
    the session so the booking page can render it without the client
    having to resend it.
    """

    def post(self, request):
        review_request, errors = validate_review_payload(dict(request.data))

        if errors:
            return Response(
                {
                    "success": False,
                    "error_code": "invalid_review_request",
                    "error_message": " ".join(errors),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        result: HotelReviewResult = HotelService().review(review_request)

        if not result.success:
            return _error_response(result.error_code, result.error_message)

        normalized = asdict(result.review)
        request.session["hotel_review"] = normalized
        return Response({"success": True, "review": normalized}, status=status.HTTP_200_OK)


class HotelBookApiView(APIView):
    """
    POST /api/v1/hotels/book/

    Step 4 - commits the booking using the bookingId from Review.
    Sending `amount` triggers Instant Booking; omitting it places a
    Hold (confirm-book is not implemented by this integration, so
    holds cannot currently be confirmed through it).
    """

    def post(self, request):
        book_request, errors = validate_book_payload(dict(request.data))

        if errors:
            return Response(
                {
                    "success": False,
                    "error_code": "invalid_book_request",
                    "error_message": " ".join(errors),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = BookingSupplierManager.get_provider().book(book_request)
        except ProviderNotConfiguredError as exc:
            return _error_response("hotel_provider_not_configured", str(exc))
        except ProviderUpstreamError as exc:
            return _error_response("hotel_provider_error", str(exc))
        except ProviderError as exc:
            return _error_response("hotel_provider_error", str(exc))

        request.session["hotel_book_result"] = asdict(result)
        return Response(
            {"success": True, "booking_id": result.booking_id, "accepted": result.accepted},
            status=status.HTTP_200_OK,
        )


class HotelBookingDetailsApiView(APIView):
    """
    POST /api/v1/hotels/booking-details/

    Fetches current booking status. Book confirmation is async (up to
    ~180s) - the confirmation page polls this endpoint every 5 seconds
    until a terminal status is returned.
    """

    def post(self, request):
        booking_id = str(request.data.get("booking_id") or request.data.get("bookingId") or "").strip()

        if not booking_id:
            return Response(
                {
                    "success": False,
                    "error_code": "invalid_booking_details_request",
                    "error_message": "booking_id is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            details = BookingSupplierManager.get_provider().booking_details(booking_id)
        except ProviderNotConfiguredError as exc:
            return _error_response("hotel_provider_not_configured", str(exc))
        except ProviderUpstreamError as exc:
            return _error_response("hotel_provider_error", str(exc))
        except ProviderError as exc:
            return _error_response("hotel_provider_error", str(exc))

        return Response({"success": True, "details": asdict(details)}, status=status.HTTP_200_OK)
