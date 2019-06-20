from src.Module.Species import Species
from src.Blueprint.Blueprint import BlueprintNode
from src.Graph import Node
from src.NeuralNetwork.Net import ModuleNet

from src.NeuralNetwork import Evaluator
import torch.tensor


class Generation:
    numBlueprints = 1
    numModules = 5

    def __init__(self, first_gen=False, previous_generation=None):
        self.speciesNumbers = []
        self.speciesCollection = {} # hashmap from species number to species
        self.blueprintCollection = set()

        if first_gen:
            self.initialise_population()
        else:
            self.generate_from_previous_generation(previous_generation)

    def initialise_population(self):
        print("initialising random population")

        for b in range(self.numBlueprints):
            blueprint = Node.gen_node_graph(BlueprintNode, "linear",linear_count= 6 )
            self.blueprintCollection.add(blueprint)

        species = Species()
        species.initialise_modules(self.numModules)
        self.speciesCollection[species.speciesNumber] = species
        self.speciesNumbers.append(species.speciesNumber)

    def generate_from_previous_generation(self, previous_gen):
        pass

    def evaluate(self, device=torch.device("cuda:0"), print_graphs = True):
        inputs, targets = Evaluator.sample_data('mnist', '../../data', device=device)

        for blueprint in self.blueprintCollection:

            module_graph = blueprint.parseto_module(self)
            module_graph.create_layers(in_features=1, device=device)
            module_graph.insert_aggregator_nodes()
            if(print_graphs):
                module_graph.plot_tree()

            net = ModuleNet(module_graph).to(device)
            net.specify_output_dimensionality(inputs, device=device)


            Evaluator.evaluate(net, 15, dataset='mnist', path='../../data', device=device, batch_size= 256)
            #batchsize:128, time:255, max GPU: 12, acc: 97.5
            #batchsize:256, time:217, max GPU: 12, acc: 96.5
            #batchsize:512, time:216, max GPU: 12, acc: 94.5

