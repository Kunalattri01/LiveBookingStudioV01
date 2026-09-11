from ..services.dto import HotelDetailRequest, HotelReviewRequest, HotelSearchRequest, NormalizedHotelDetail, NormalizedHotelReview
from .base import HotelProvider
from .exceptions import ProviderNotConfiguredError

_MESSAGE = (
    "No hotel provider is configured. Set HOTEL_PROVIDER to a "
    "supported value (currently: 'tripjack') and configure "
    "TRIPJACK_API_KEY / HOTEL_HMS_BASE_URL / HOTEL_BOOKER_BASE_URL."
)


class UnconfiguredHotelProvider(HotelProvider):
    """
    Used for ALL real web/mobile traffic whenever no real hotel
    supplier is configured (HOTEL_PROVIDER is unset, set to
    'unconfigured', or set to any value SupplierManager doesn't
    recognize as a real provider).

    This NEVER returns hotel data - only a controlled error.
    """

    def search(self, search_request: HotelSearchRequest) -> dict:
        raise ProviderNotConfiguredError(_MESSAGE)

    def detail(self, detail_request: HotelDetailRequest) -> NormalizedHotelDetail:
        raise ProviderNotConfiguredError(_MESSAGE)

    def review(self, review_request: HotelReviewRequest) -> NormalizedHotelReview:
        raise ProviderNotConfiguredError(_MESSAGE)
