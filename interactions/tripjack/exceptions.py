class TripJackError(Exception):
    """Base exception for TripJack connectivity issues."""


class TripJackNotConfiguredError(TripJackError):
    """Raised when TRIPJACK_API_KEY / TRIPJACK_BASE_URL are not set."""


class TripJackRequestError(TripJackError):
    """Raised when a TripJack HTTP request fails (network/timeout/etc)."""
