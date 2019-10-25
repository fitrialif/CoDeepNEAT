import random
from typing import List, TYPE_CHECKING

from Genotype.NEAT.Operators.RepresentativeSelectors.RepresentativeSelector import RepresentativeSelector

if TYPE_CHECKING:
    from Genotype.NEAT.Genome import Genome


class RandomRepSelector(RepresentativeSelector):
    def select_representative(self, members: List[Genome]) -> Genome:
        return random.choice(members)