from ..normalizers.tripjack_booking import TripJackHotelBookingNormalizer
from ..services.booking_dto import HotelBookRequest, NormalizedBookingDetails, NormalizedBookResult
from .booking_base import HotelBookingProvider
from .exceptions import ProviderUpstreamError
from .tripjack_client import TripJackHotelClient
from .tripjack_exceptions import TripJackHotelError


class TripJackHotelBookingAdapter(HotelBookingProvider):
    """TripJack implementation of the Book / Booking Details steps, behind the provider/normalizer boundary."""

    def __init__(self):
        self.client = TripJackHotelClient()
        self.normalizer = TripJackHotelBookingNormalizer()

    def book(self, book_request: HotelBookRequest) -> NormalizedBookResult:
        payload = self._build_book_payload(book_request)
        try:
            raw = self.client.book(payload)
            return self.normalizer.normalize_book(raw)
        except TripJackHotelError as exc:
            raise ProviderUpstreamError(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise ProviderUpstreamError("Hotel booking response could not be normalized.") from exc

    def booking_details(self, booking_id: str) -> NormalizedBookingDetails:
        try:
            raw = self.client.booking_details(booking_id)
            return self.normalizer.normalize_booking_details(raw)
        except TripJackHotelError as exc:
            raise ProviderUpstreamError(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise ProviderUpstreamError("Hotel booking-details response could not be normalized.") from exc

    @staticmethod
    def _build_book_payload(book_request: HotelBookRequest) -> dict:
        payload = {
            "bookingId": book_request.booking_id,
            "roomTravellerInfo": [
                {
                    "travellerInfo": [
                        {
                            key: value
                            for key, value in {
                                "ti": traveller.title,
                                "pt": traveller.passenger_type,
                                "fN": traveller.first_name,
                                "lN": traveller.last_name,
                                "pan": traveller.pan,
                                "pNum": traveller.passport_number,
                            }.items()
                            if value is not None
                        }
                        for traveller in group.travellers
                    ]
                }
                for group in book_request.room_traveller_info
            ],
            "deliveryInfo": {
                "emails": list(book_request.delivery_info.emails),
                "contacts": list(book_request.delivery_info.contacts),
                "code": list(book_request.delivery_info.codes),
            },
            "type": "HOTEL",
        }

        if book_request.gst_info and (book_request.gst_info.gst_number or book_request.gst_info.registered_name):
            payload["gstInfo"] = {
                "gstNumber": book_request.gst_info.gst_number,
                "registeredName": book_request.gst_info.registered_name,
            }

        if book_request.amount is not None:
            payload["paymentInfos"] = [{"amount": book_request.amount}]

        return payload
