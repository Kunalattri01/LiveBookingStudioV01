from django.conf import settings

from .booking_base import HotelBookingProvider
from .exceptions import ProviderNotConfiguredError
from .mock_provider import MockHotelBookingProvider
from .tripjack_booking_provider import TripJackHotelBookingAdapter

# See providers/manager.py for why "mock" is registered here.
_REGISTERED_BOOKING_PROVIDERS = {
    "tripjack": TripJackHotelBookingAdapter,
    "mock": MockHotelBookingProvider,
}


class BookingSupplierManager:
    """Select the configured hotel booking supplier without exposing it to views."""

    @staticmethod
    def get_provider() -> HotelBookingProvider:
        provider_name = (getattr(settings, "HOTEL_PROVIDER", "unconfigured") or "").strip().lower()
        provider_class = _REGISTERED_BOOKING_PROVIDERS.get(provider_name)
        if provider_class is None:
            raise ProviderNotConfiguredError("No real hotel booking provider is configured.")
        return provider_class()
