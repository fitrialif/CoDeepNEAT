import copy
import random

from src2.Genotype.NEAT.Connection import Connection
from src2.Genotype.NEAT.Genome import Genome
from src2.Genotype.NEAT.Node import Node, NodeType
from src2.Genotype.NEAT.Operators.Mutations import MutationRecord
from src2.Genotype.NEAT.Operators.Mutations.Mutator import Mutator


class GenomeMutator(Mutator):

    """
    performs the base set of mutations to the general genome object
    """

    def mutate(self, genome: Genome, mutation_record: MutationRecord):
        raise NotImplementedError("Implement mutate method in all super classes")

    def mutate_base_genome(self, genome: Genome,mutation_record : MutationRecord, add_node_chance: float,
                           add_connection_chance: float, allow_disabling_connections: bool = False):

        """performs base NEAT genome mutations, as well as node and genome property mutations"""

        if random.random() < add_node_chance:
            self.add_node_mutation(genome,mutation_record)

        if random.random() < add_connection_chance:
            self.add_connection_mutation(genome,mutation_record)

        if allow_disabling_connections:
            """randomly deactivates and reactivates connections"""
            for connection in genome.connections.values():
                orig_conn = copy.deepcopy(connection)
                connection.mutate()#this is the call which enables/disables connections
                # If mutation made the genome invalid then undo it
                if not genome.validate():
                    """
                        disabling the connection lead to a disconnected graph
                        or enabling the connection lead to a cycle
                    """
                    genome.connections[orig_conn.id] = orig_conn

        for node in genome.nodes.values():
            """mutates node properties"""
            node.mutate()

        for mutagen in genome.get_all_mutagens():
            """mutates the genome level properties"""
            mutagen.mutate()



    def add_connection_mutation(self, genome: Genome, mutation_record : MutationRecord):
        """tries a few times to randomly add a new connection to the genome"""

        tries = 10

        added_connection = False
        while not added_connection and tries >0:
            """
                tries to randomly add a new connection to the genome
                a new random connection can be rejected if it is already in the genome, 
                    or it tries to connect a node to itself
                    or it tries to connect to an input node
                    or it tries to connect to an output node
                    or it creates a cycle
            """
            added_connection = self.test_and_add_connection(genome,mutation_record, random.choice(list(genome.nodes.values())),random.choice(list(genome.nodes.values())))
            tries-=1

        return added_connection

    def test_and_add_connection(self,genome: Genome ,mutation_record : MutationRecord, from_node : Node, to_node: Node):
        """
            Adds a connection between to nodes if possible
            creates a copy genome, adds the node, checks for cycles in the copy
            if no cycles, the connection is added to the original genome

            :returns whether or not the candidate connection was added to the original genome
        """

        copy_genome = copy.deepcopy(genome)

        # Validation
        if from_node.id == to_node.id:
            return False

        candidate_connection = (from_node.id, to_node.id)

        if candidate_connection in genome.connected_nodes:
            """
                this connection is already in the genome
            """
            return False

        if from_node.node_type == NodeType.OUTPUT:
            return False

        if to_node.node_type == NodeType.INPUT:
            return False

        # Adding to global mutation dictionary
        if mutation_record.exists(candidate_connection):
            mutation_id = mutation_record.mutations[candidate_connection]
        else:
            mutation_id = mutation_record.add_mutation(candidate_connection)

        # Adding new mutation
        mutated_conn = Connection(mutation_id, from_node.id, to_node.id)

        copy_genome.add_connection(mutated_conn)
        if copy_genome.has_cycle():
            """the candidate connection creates a cycle"""
            return False

        """by now the candidate connection is valid"""
        genome.add_connection(mutated_conn)

        return True


    def add_node_mutation(self, genome: Genome, mutation_record : MutationRecord):
        """Adds a node on a connection and updates the relevant genome"""
        tries = 10

        added_node = False
        while not added_node and tries > 0:
            """
                tries to randomly add a new node onto a connection in the genome
                a new random node can be rejected if is already in the genome
            """
            added_node = self.test_and_add_node_on_connection(genome, mutation_record,
                                                            random.choice(list(genome.connections.values())))
            tries -= 1

        return added_node


    def test_and_add_node_on_connection(self, genome: Genome, mutation_record : MutationRecord, connection:Connection):
        mutation_id = connection.id

        if mutation_record.exists(mutation_id):
            """this node mutation has occurred before"""
            mutated_node_id = mutation_record.mutations[mutation_id]#the id of the original node which was placed on this connection
            if mutated_node_id in genome.nodes:  # this connection has already created a new node
                return False

            # the id of the connection which brides to the new node
            into_node_connection_id = mutation_record.mutations[(self.from_node, mutated_node_id)]
            # the id of the connection which brides from the new node
            out_of_node_connection_id = mutation_record.mutations[(mutated_node_id, self.to_node)]


        else:
            """if this mutation hasn't occurred before if should not be in any genome"""

            mutated_node_id = mutation_record.add_mutation(mutation_id)
            if mutated_node_id in genome.nodes:  # this connection has already created a new node
                raise Exception("node mutation not in mutation record, but in a genome")

            into_node_connection_id = mutation_record.add_mutation((self.from_node, mutated_node_id))
            out_of_node_connection_id = mutation_record.add_mutation((mutated_node_id, self.to_node))

        NodeType = type(list(genome.nodes.values())[0])#node could be a blueprint, module or da node
        mutated_node = NodeType(mutated_node_id)#multiple node objects share the same id. indicating they are functionally the same

        genome.add_node(mutated_node)

        mutated_from_conn = Connection(into_node_connection_id, self.from_node, mutated_node_id)
        mutated_to_conn = Connection(out_of_node_connection_id, mutated_node_id, self.to_node)

        genome.add_connection(mutated_from_conn)
        genome.add_connection(mutated_to_conn)

        connection.enabled.set_value(False)

        return True