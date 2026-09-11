from typing import Any, Dict, List

from interactions.tripjack.client import TripJackClient
from interactions.tripjack.exceptions import TripJackError

from ..normalizers.tripjack_booking import TripJackBookingNormalizer
from ..services.booking import NormalizedReview, NormalizedSeatMap
from .booking_base import FlightBookingProvider
from .exceptions import ProviderUpstreamError


class TripJackBookingAdapter(FlightBookingProvider):
    """TripJack implementation behind the provider/normalizer boundary."""

    def __init__(self):
        self.client = TripJackClient()
        self.normalizer = TripJackBookingNormalizer()

    def review(self, price_ids: List[str]) -> NormalizedReview:
        try:
            raw = self.client.review_fares(price_ids)
            return self.normalizer.normalize_review(raw)
        except TripJackError as exc:
            raise ProviderUpstreamError(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise ProviderUpstreamError("Flight review response could not be normalized.") from exc

    def seat_map(self, booking_id: str) -> NormalizedSeatMap:
        try:
            raw = self.client.seat_map(booking_id)
            return self.normalizer.normalize_seat_map(raw)
        except TripJackError as exc:
            raise ProviderUpstreamError(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise ProviderUpstreamError("Seat-map response could not be normalized.") from exc

    def fare_rule(self, reference_id: str, flow_type: str = "SEARCH") -> Dict[str, Any]:
        try:
            raw = self.client.fare_rule(reference_id, flow_type)
            return self.normalizer.normalize_fare_rule(raw)
        except TripJackError as exc:
            raise ProviderUpstreamError(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise ProviderUpstreamError("Fare-rule response could not be normalized.") from exc
