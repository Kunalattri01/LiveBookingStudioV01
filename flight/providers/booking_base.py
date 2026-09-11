from abc import ABC, abstractmethod
from typing import Any, Dict, List

from ..services.booking import NormalizedReview, NormalizedSeatMap


class FlightBookingProvider(ABC):
    """Provider-independent interface for post-search flight operations."""

    @abstractmethod
    def review(self, price_ids: List[str]) -> NormalizedReview:
        raise NotImplementedError

    @abstractmethod
    def seat_map(self, booking_id: str) -> NormalizedSeatMap:
        raise NotImplementedError

    @abstractmethod
    def fare_rule(self, reference_id: str, flow_type: str = "SEARCH") -> Dict[str, Any]:
        raise NotImplementedError
