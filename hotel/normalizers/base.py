from abc import ABC, abstractmethod
from typing import Any, Dict

from ..services.booking_dto import NormalizedBookingDetails, NormalizedBookResult
from ..services.dto import NormalizedHotelDetail, NormalizedHotelReview


class HotelNormalizer(ABC):
    """Interface every hotel supplier normalizer must implement for the search-side flow."""

    @abstractmethod
    def normalize_listing(self, raw_response: Dict[str, Any]) -> dict:
        """
        Returns a dict with keys: hotels (List[NormalizedHotel]),
        correlation_id, currency, nationality, total_results - the
        pieces HotelService assembles into a HotelSearchResult.
        """
        raise NotImplementedError

    @abstractmethod
    def normalize_detail(self, raw_response: Dict[str, Any]) -> NormalizedHotelDetail:
        raise NotImplementedError

    @abstractmethod
    def normalize_review(self, raw_response: Dict[str, Any]) -> NormalizedHotelReview:
        raise NotImplementedError


class HotelBookingNormalizer(ABC):
    """Interface every hotel supplier normalizer must implement for the post-review flow."""

    @abstractmethod
    def normalize_book(self, raw_response: Dict[str, Any]) -> NormalizedBookResult:
        raise NotImplementedError

    @abstractmethod
    def normalize_booking_details(self, raw_response: Dict[str, Any]) -> NormalizedBookingDetails:
        raise NotImplementedError
