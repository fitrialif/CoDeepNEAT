from typing import List, Dict

import math
import random

from src2.Genotype.NEAT.Operators.RepresentativeSelectors.RepresentativeSelector import RepresentativeSelector
from src2.Genotype.NEAT.Genome import Genome
from Genotype.NEAT import MutationRecord
from src2.Configuration import config
from src2.Genotype.NEAT.Operators.Selectors import Selector
from src2.Genotype.NEAT.Operators.Mutations import Mutator
import src2.Genotype.NEAT.Operators.Cross as Cross


class Species:
    species_id = 0

    # These are set in the populations init method
    selector: Selector
    mutator: Mutator
    representative_selector: RepresentativeSelector

    def __init__(self, representative: Genome):
        self.id: int = Species.species_id
        Species.species_id += 1

        self.representative: Genome = representative
        self.members: Dict[int, Genome] = {representative.id: representative}
        self.ranked_members: List[int] = [representative.id]
        self.next_species_size: int = 1000
        # self.fitness: int = -1  # TODO is this ever used
        self.max_fitness_ties: int = 0  # a count of how many ties there are for the top accuracy

    def __iter__(self):
        return iter(self.members)

    def __len__(self):
        return len(self.members)

    def __getitem__(self, id: int):
        return self.members[id]

    def __repr__(self):
        return 'Species has ' + repr(len(self.members)) + ' members of type: ' + repr(
            type(list(self.members.values())[0]))

    def add(self, individual: Genome):
        self.members[individual.id] = individual

    def sample_individual(self) -> Genome:
        """:return a random individual from the species"""
        return random.choice(self.members.values())

    def _get_num_elite(self) -> int:
        """
        Finds the number of elite this population should have, given the desired number of elite, population size and
        number of ties there are for members with the best fitness
        """
        elite = min(config.elite, len(self.members))
        highest_acc = self.members[self.ranked_members[0]].fitness_values[0]
        self.max_fitness_ties = sum(
            genome.fitness_values[0] == highest_acc for genome in self.members.values())  # TODO test
        return max(elite, self.max_fitness_ties)

    def _unfill(self):
        """Removes all poorly performing genomes"""
        self.ranked_members = self.ranked_members[:math.ceil(len(self.ranked_members) * config.reproduce_percent)]
        survivors = set(self.ranked_members)
        new_members = {}
        for id in self.members.keys():
            if id in survivors:
                new_members[id] = self.members[id]

        self.members = new_members

    def _fill(self, mutation_record: MutationRecord):
        """Fills species until it has next_species_size members, using crossover and mutation"""
        children: List[Genome] = []
        num_elite = self._get_num_elite()
        # Species.selector.before_selection(self.members) todo do we need this

        while len(children) < self.next_species_size - num_elite:
            p1, p2 = Species.selector.select(ranked_genomes=self.ranked_members, genomes=self.members)
            child = Cross.over(p1, p2)
            Species.mutator.mutate(child, mutation_record)
            children.append(child)

        self.members = {id: self.members[id] for id in self.ranked_members[:num_elite]}  # adds in elite
        self.members = {**self.members, **{child.id: child for child in children}}  # adds in children

    def step(self, mutation_record: MutationRecord):
        """Runs a single generation of evolution"""
        if not self.members:
            raise Exception('Cannot step empty species')

        if self.next_species_size == 0:
            """this species has been extincted"""
            self.members = {}
            self.ranked_members = []
            return

        # note original CoDeepNEAT checks for equal fitness's and prioritizes genomes with more genes
        self.ranked_members = [id for id in self.members.keys()]
        self.ranked_members.sort(
            key=lambda id: self.members[id].rank)  # TODO might need to reverse depends how we set rank
        self._unfill()
        self._fill(mutation_record)

        self.representative = Species.representative_selector.select_representative(self.members)
