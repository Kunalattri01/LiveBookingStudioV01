"""Provider-neutral normalizers for post-search booking data."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from ..services.booking import NormalizedReview, NormalizedSeatMap


class BookingNormalizer(ABC):
    """Convert supplier booking responses into application DTOs."""

    @abstractmethod
    def normalize_review(self, raw_response: Dict[str, Any]) -> NormalizedReview:
        raise NotImplementedError

    @abstractmethod
    def normalize_seat_map(self, raw_response: Dict[str, Any]) -> NormalizedSeatMap:
        raise NotImplementedError

    @abstractmethod
    def normalize_fare_rule(self, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
