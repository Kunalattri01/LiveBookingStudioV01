from abc import ABC, abstractmethod

from ..services.dto import HotelDetailRequest, HotelReviewRequest, HotelSearchRequest, NormalizedHotelDetail, NormalizedHotelReview


class HotelProvider(ABC):
    """
    Interface every hotel supplier adapter (or safety placeholder) must
    implement for the search-side flow. HotelService and
    SupplierManager only ever depend on this interface, never on a
    concrete provider.
    """

    @abstractmethod
    def search(self, search_request: HotelSearchRequest) -> dict:
        """
        Step 1 - Listing. Returns a dict with keys: hotels
        (List[NormalizedHotel]), correlation_id, currency, nationality,
        total_results.

        Implementations must raise hotel.providers.exceptions.ProviderError
        (or a subclass) on failure rather than returning fabricated data.
        """
        raise NotImplementedError

    @abstractmethod
    def detail(self, detail_request: HotelDetailRequest) -> NormalizedHotelDetail:
        """Step 2 - Dynamic Detail (Pricing) for a single hotel."""
        raise NotImplementedError

    @abstractmethod
    def review(self, review_request: HotelReviewRequest) -> NormalizedHotelReview:
        """Step 3 - Review: re-validates price/availability for one option."""
        raise NotImplementedError
