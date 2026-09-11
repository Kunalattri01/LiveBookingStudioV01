from typing import List

from ..services.dto import SearchRequest, NormalizedFlight
from .base import FlightProvider
from .exceptions import ProviderNotConfiguredError


class UnconfiguredProvider(FlightProvider):
    """
    Used for ALL real web/mobile traffic whenever no real flight
    supplier is configured (FLIGHT_PROVIDER is unset, set to
    'unconfigured', or set to any value SupplierManager doesn't
    recognize as a real provider).

    This NEVER returns flight data - only a controlled error. This is
    the only safe default for production and for any environment
    where TripJack (or another approved provider) isn't wired up yet.
    """

    def search(self, search_request: SearchRequest) -> List[NormalizedFlight]:
        raise ProviderNotConfiguredError(
            "No flight provider is configured. Set FLIGHT_PROVIDER to a "
            "supported value (currently: 'tripjack') once TripJack "
            "credentials/documentation are available."
        )
