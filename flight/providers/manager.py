from django.conf import settings

from .base import FlightProvider
from .tripjack_provider import TripJackAdapter
from .unconfigured_provider import UnconfiguredProvider

# Only real, production-safe providers are registered here.
# MockFlightProvider is intentionally absent - it must never be
# reachable through configuration, only injected directly by tests.
_REGISTERED_PROVIDERS = {
    "tripjack": TripJackAdapter,
}


class SupplierManager:
    """
    Selects the active flight provider based on the FLIGHT_PROVIDER
    setting. Any value that isn't a registered real provider - unset,
    "unconfigured", a typo, or anything else - safely resolves to
    UnconfiguredProvider, which never returns flight data.

    There is no configuration path to the mock provider.
    """

    @staticmethod
    def get_provider() -> FlightProvider:
        provider_name = (getattr(settings, "FLIGHT_PROVIDER", "unconfigured") or "").strip().lower()

        provider_class = _REGISTERED_PROVIDERS.get(provider_name)

        if provider_class is None:
            return UnconfiguredProvider()

        return provider_class()
