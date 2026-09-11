from abc import ABC, abstractmethod
from typing import List

from ..services.dto import SearchRequest, NormalizedFlight


class FlightProvider(ABC):
    """
    Interface every flight supplier adapter (or safety placeholder)
    must implement. FlightService and SupplierManager only ever depend
    on this interface, never on a concrete provider.
    """

    @abstractmethod
    def search(self, search_request: SearchRequest) -> List[NormalizedFlight]:
        """
        Perform a flight search and return already-normalized flights.

        Implementations must raise flight.providers.exceptions.ProviderError
        (or a subclass) on failure rather than returning fabricated data.
        """
        raise NotImplementedError
