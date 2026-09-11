from django.conf import settings

from .base import HotelProvider
from .mock_provider import MockHotelProvider
from .tripjack_provider import TripJackHotelAdapter
from .unconfigured_provider import UnconfiguredHotelProvider

# "mock" is a deliberate, explicit exception to the usual rule (see
# flight/providers/manager.py) that a mock provider is never reachable
# via configuration. It's registered here ONLY because TripJack's UAT
# sandbox currently has no stable live inventory to demo against - see
# hotel/providers/mock_provider.py's docstring. It is never the
# default ("unconfigured" is) and must be set explicitly.
_REGISTERED_PROVIDERS = {
    "tripjack": TripJackHotelAdapter,
    "mock": MockHotelProvider,
}


class SupplierManager:
    """
    Selects the active hotel provider based on the HOTEL_PROVIDER
    setting. Any value that isn't a registered real provider - unset,
    "unconfigured", a typo, or anything else - safely resolves to
    UnconfiguredHotelProvider, which never returns hotel data.
    """

    @staticmethod
    def get_provider() -> HotelProvider:
        provider_name = (getattr(settings, "HOTEL_PROVIDER", "unconfigured") or "").strip().lower()

        provider_class = _REGISTERED_PROVIDERS.get(provider_name)

        if provider_class is None:
            return UnconfiguredHotelProvider()

        return provider_class()
