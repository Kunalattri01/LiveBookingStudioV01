from typing import Optional

from .dto import SearchRequest, SearchResult
from ..providers.base import FlightProvider
from ..providers.exceptions import (
    ProviderError,
    ProviderNotConfiguredError,
    ProviderUnsupportedRequestError,
    ProviderUpstreamError,
)
from ..providers.manager import SupplierManager


class FlightService:
    """
    Single entry point for performing a flight search. Contains no
    provider-specific logic - only orchestration:

        validate (done by caller via validators.py)
            -> SupplierManager.get_provider() [or injected provider]
            -> provider.search()
            -> SearchResult

    Automated tests may inject an explicit provider (e.g.
    MockFlightProvider) via the constructor. Real application code
    must never do this - it must always go through SupplierManager,
    which is the only thing that decides which real provider (if any)
    is active.
    """

    def __init__(self, provider: Optional[FlightProvider] = None):
        self._injected_provider = provider

    def _get_provider(self) -> FlightProvider:
        if self._injected_provider is not None:
            return self._injected_provider
        return SupplierManager.get_provider()

    def search(self, search_request: SearchRequest) -> SearchResult:
        provider = self._get_provider()

        try:
            flights = provider.search(search_request)
        except ProviderNotConfiguredError as exc:
            return SearchResult(
                success=False,
                flights=[],
                error_code="flight_provider_not_configured",
                error_message=str(exc),
            )
        except ProviderUnsupportedRequestError as exc:
            return SearchResult(
                success=False,
                flights=[],
                error_code="provider_search_not_supported",
                error_message=str(exc),
            )
        except ProviderUpstreamError as exc:
            return SearchResult(
                success=False,
                flights=[],
                error_code="flight_provider_error",
                error_message=str(exc),
            )
        except ProviderError as exc:
            # Any other provider failure we didn't specifically
            # categorize - still a controlled error, never fake data.
            return SearchResult(
                success=False,
                flights=[],
                error_code="flight_provider_error",
                error_message=str(exc),
            )

        return SearchResult(success=True, flights=flights)
