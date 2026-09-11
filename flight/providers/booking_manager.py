from django.conf import settings

from .booking_base import FlightBookingProvider
from .exceptions import ProviderNotConfiguredError
from .tripjack_booking_provider import TripJackBookingAdapter


_REGISTERED_BOOKING_PROVIDERS = {"tripjack": TripJackBookingAdapter}


class BookingSupplierManager:
    """Select the configured booking supplier without exposing it to views."""

    @staticmethod
    def get_provider() -> FlightBookingProvider:
        provider_name = (getattr(settings, "FLIGHT_PROVIDER", "unconfigured") or "").strip().lower()
        provider_class = _REGISTERED_BOOKING_PROVIDERS.get(provider_name)
        if provider_class is None:
            raise ProviderNotConfiguredError("No real flight booking provider is configured.")
        return provider_class()
