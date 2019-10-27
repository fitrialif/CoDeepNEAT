from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from src2.Genotype.NEAT.Genome import Genome


class Selector(ABC):
    @abstractmethod
    def select(self, genomes: List[Genome]) -> Tuple[Genome, Genome]:
        pass
