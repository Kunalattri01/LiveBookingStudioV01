from typing import Optional

from ..models import Hotel
from ..providers.base import HotelProvider
from ..providers.exceptions import (
    ProviderError,
    ProviderNotConfiguredError,
    ProviderUnsupportedRequestError,
    ProviderUpstreamError,
)
from ..providers.manager import SupplierManager
from .dto import (
    HotelDetailRequest,
    HotelDetailResult,
    HotelReviewRequest,
    HotelReviewResult,
    HotelSearchRequest,
    HotelSearchResult,
)

_ERROR_CODE_BY_EXCEPTION = {
    ProviderNotConfiguredError: "hotel_provider_not_configured",
    ProviderUnsupportedRequestError: "provider_request_not_supported",
    ProviderUpstreamError: "hotel_provider_error",
}


class HotelService:
    """
    Single entry point for the search-side hotel flow (Listing,
    Pricing, Review). Contains no provider-specific logic - only
    orchestration:

        validate (done by caller via services/validators.py)
            -> SupplierManager.get_provider() [or injected provider]
            -> provider.search()/.detail()/.review()
            -> *Result

    Automated tests may inject an explicit provider via the
    constructor. Real application code must always go through
    SupplierManager, which is the only thing that decides which real
    provider (if any) is active.
    """

    def __init__(self, provider: Optional[HotelProvider] = None):
        self._injected_provider = provider

    def _get_provider(self) -> HotelProvider:
        if self._injected_provider is not None:
            return self._injected_provider
        return SupplierManager.get_provider()

    @staticmethod
    def _error_code_for(exc: ProviderError) -> str:
        for exc_type, code in _ERROR_CODE_BY_EXCEPTION.items():
            if isinstance(exc, exc_type):
                return code
        return "hotel_provider_error"

    def search(self, search_request: HotelSearchRequest) -> HotelSearchResult:
        provider = self._get_provider()

        try:
            result = provider.search(search_request)
        except ProviderError as exc:
            return HotelSearchResult(
                success=False, error_code=self._error_code_for(exc), error_message=str(exc)
            )

        hotels = result.get("hotels") or []
        self._attach_images(hotels)

        return HotelSearchResult(success=True, **result)

    def detail(self, detail_request: HotelDetailRequest) -> HotelDetailResult:
        provider = self._get_provider()

        try:
            detail = provider.detail(detail_request)
        except ProviderError as exc:
            return HotelDetailResult(
                success=False, error_code=self._error_code_for(exc), error_message=str(exc)
            )

        self._attach_images([detail])

        return HotelDetailResult(success=True, detail=detail)

    @staticmethod
    def _attach_images(hotels) -> None:
        """
        Attaches image_url and star_rating from the local Hotel catalog
        onto each normalized hotel/detail object, in place. TripJack's
        Listing/Pricing responses never include either - only the
        separate static-content endpoints do (see
        hotel/management/commands/seed_tripjack_hotels.py) - so the
        local catalog is the only source for both in this app.
        """
        ids = [h.tj_hotel_id for h in hotels if getattr(h, "tj_hotel_id", None)]
        if not ids:
            return

        catalog_by_id = {
            row["tj_hotel_id"]: row
            for row in Hotel.objects.filter(tj_hotel_id__in=ids).values(
                "tj_hotel_id", "image_url", "star_rating"
            )
        }
        for hotel in hotels:
            row = catalog_by_id.get(hotel.tj_hotel_id)
            hotel.image_url = (row.get("image_url") or None) if row else None
            hotel.star_rating = row.get("star_rating") if row else None

    def review(self, review_request: HotelReviewRequest) -> HotelReviewResult:
        provider = self._get_provider()

        try:
            review = provider.review(review_request)
        except ProviderError as exc:
            return HotelReviewResult(
                success=False, error_code=self._error_code_for(exc), error_message=str(exc)
            )

        return HotelReviewResult(success=True, review=review)
