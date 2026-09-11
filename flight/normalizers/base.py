from abc import ABC, abstractmethod
from typing import List

from ..services.dto import NormalizedFlight


class Normalizer(ABC):
    """
    Converts a raw supplier response into our internal
    NormalizedFlight representation. One implementation per supplier.
    """

    @abstractmethod
    def normalize(self, raw_response: dict) -> List[NormalizedFlight]:
        raise NotImplementedError
