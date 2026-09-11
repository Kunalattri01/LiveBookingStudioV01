class ProviderError(Exception):
    """Base exception for any hotel provider failure."""


class ProviderNotConfiguredError(ProviderError):
    """
    Raised when no real hotel provider is configured (or an unknown
    HOTEL_PROVIDER value is set). This must always be handled as a
    controlled error - never as a signal to fall back to fake data.
    """


class ProviderUnsupportedRequestError(ProviderError):
    """
    Raised when a provider IS configured but does not support the
    specific request shape it was asked to handle.
    """


class ProviderUpstreamError(ProviderError):
    """
    Raised when a configured, supported provider request failed at the
    supplier: timeout, connection failure, non-200 HTTP response,
    malformed/unexpected JSON, or the supplier's own reported failure
    status. Never carries the supplier's raw credentials or headers.
    """
