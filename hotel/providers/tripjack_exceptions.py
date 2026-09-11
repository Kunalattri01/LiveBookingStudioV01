class TripJackHotelError(Exception):
    """Base exception for TripJack Hotel API connectivity issues."""


class TripJackHotelNotConfiguredError(TripJackHotelError):
    """Raised when the TripJack API key / hotel base URLs are not set."""


class TripJackHotelRequestError(TripJackHotelError):
    """Raised when a TripJack Hotel API request fails (network/timeout/HTTP/JSON/etc)."""
