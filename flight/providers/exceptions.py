class ProviderError(Exception):
    """Base exception for any flight provider failure."""


class ProviderNotConfiguredError(ProviderError):
    """
    Raised when no real flight provider is configured (or an unknown
    FLIGHT_PROVIDER value is set). This must always be handled as a
    controlled error - never as a signal to fall back to fake data.
    """


class ProviderUnsupportedRequestError(ProviderError):
    """
    Raised when a provider IS configured but does not (yet) support
    the specific request shape - e.g. TripJack round-trip/multi-city
    response handling is unverified and intentionally not implemented.
    Distinct from ProviderNotConfiguredError: the provider exists and
    works for other request shapes.
    """


class ProviderUpstreamError(ProviderError):
    """
    Raised when a configured, supported provider request failed at the
    supplier: timeout, connection failure, non-200 HTTP response,
    malformed/unexpected JSON, or the supplier's own reported failure
    status. Never carries the supplier's raw credentials or headers.
    """
