from abc import ABC, abstractmethod

from ..services.booking_dto import HotelBookRequest, NormalizedBookingDetails, NormalizedBookResult


class HotelBookingProvider(ABC):
    """Provider-independent interface for post-review hotel operations."""

    @abstractmethod
    def book(self, book_request: HotelBookRequest) -> NormalizedBookResult:
        """Step 4 - Book: commits (or holds) the booking."""
        raise NotImplementedError

    @abstractmethod
    def booking_details(self, booking_id: str) -> NormalizedBookingDetails:
        """Fetches current booking status - used to poll for confirmation after Book."""
        raise NotImplementedError
